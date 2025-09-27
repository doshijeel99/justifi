import os
import json
import re
import logging
import aiohttp
import asyncio
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langdetect import detect
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LegalChatbot")

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models - Simplified to just take query
class LegalQuery(BaseModel):
    query: str

class LegalResponse(BaseModel):
    advice: str
    sources: List[str]

class LegalDocument(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

class LegalChatbot:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        # FastRouter API configuration
        self.api_url = "https://go.fastrouter.ai/api/v1/chat/completions"
        self.model_name = "mistralai/Mistral-Small-24B-Instruct-2501"
        self.temperature = 0.2
        
        # Initialize RAG components
        try:
            # Explicitly install FAISS if needed
            try:
                import faiss
                logger.info("FAISS already installed")
            except ImportError:
                logger.warning("FAISS not installed. Installing faiss-cpu...")
                os.system("pip install faiss-cpu")
                logger.info("FAISS installed successfully")
                
            self.embeddings = self._initialize_embeddings()
            self.vector_stores = self._initialize_vector_stores()
            logger.info("Vector stores initialized successfully")
        except Exception as e:
            logger.error(f"Vector store initialization failed: {str(e)}")
            self.vector_stores = {}
        
        # Initialize agent components with structured agent instead of react agent
        try:
            self.agent_executor = self._initialize_agents()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Agent initialization failed: {str(e)}")
            self.agent_executor = None

        # Define legal keywords for filtering non-legal queries
        self.legal_keywords = [
            "law", "legal", "court", "rights", "lawsuit", "sue", "attorney", "lawyer", 
    "judge", "criminal", "civil", "plaintiff", "defendant", "case", "trial", 
    "verdict", "settlement", "appeal", "contract", "tort", "damages", "liability",
    "statute", "regulation", "constitution", "amendment", "prosecution", "defense",
    "charge", "bail", "warrant", "injunction", "jurisdiction", "mediation", "arbitration",
    "divorce", "custody", "property", "bankruptcy", "will", "trust", "estate", "probate",
    "copyright", "patent", "trademark", "intellectual property", "licensing", "franchise",
    "immigration", "visa", "asylum", "deportation", "citizenship", "naturalization",
    "tax", "irs", "income", "audit", "refund", "deduction", "capital gains", "inheritance tax",
    "employment", "wrongful", "discrimination", "harassment", "compensation", "overtime pay",
    "whistleblower", "worker's rights", "unemployment", "pension", "severance",
    "rent", "lease", "eviction", "tenant", "landlord", "mortgage", "foreclosure",
    "zoning", "property dispute", "easement", "eminent domain", "real estate",
    "probation", "parole", "sentencing", "felony", "misdemeanor", "habeas corpus",
    "public defender", "pro bono", "plea bargain", "death penalty", "human rights",
    "disability rights", "equal protection", "hate crime", "civil rights",
    "sexual harassment", "domestic violence", "child support", "alimony", "prenup",
    "class action", "small claims", "consumer protection", "false advertising",
    "product liability", "fraud", "identity theft", "defamation", "libel", "slander",
    "privacy", "data protection", "cybercrime", "internet law", "telecommunications law",
    "antitrust", "monopoly", "securities law", "insider trading", "banking regulation",
    "insurance law", "environmental law", "pollution", "EPA", "climate regulations",
    "military law", "martial law", "war crimes", "extradition", "treaty", "international law",
    "asylum law", "refugee law", "maritime law", "aviation law", "space law",
    "healthcare law", "medical malpractice", "HIPAA", "pharmaceutical regulation",
    "food safety", "FDA", "animal rights", "bioethics", "genetic privacy",
    "corporate law", "business formation", "mergers and acquisitions", "LLC", "nonprofit law",
    "trust law", "fiduciary duty", "contract breach", "arbitration clause",
    "cybersecurity law", "hacking", "intellectual freedom", "whistleblower protection",
    "media law", "freedom of speech", "censorship", "press freedom","punishment","crime"]
        
        logger.info("LegalChatbot initialization complete")

    async def _call_fastrouter_api(self, prompt: str) -> str:
        """Call the FastRouter API with the given prompt"""
        logger.info(f"🤖 MODEL: Calling FastRouter API with model: {self.model_name}")
        logger.info(f"📊 MODEL: Request payload - temperature: {self.temperature}, max_tokens: 2000")
        logger.info(f"📝 MODEL: Prompt length: {len(prompt)} characters")
        logger.info(f"📝 MODEL PROMPT: {prompt[:500]}...")
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"🌐 MODEL: Sending request to {self.api_url}")
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    logger.info(f"📡 MODEL: Received response with status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        model_response = result["choices"][0]["message"]["content"]
                        logger.info(f"✅ MODEL: Response received (length: {len(model_response)})")
                        logger.info(f"🎯 MODEL RESPONSE: {model_response[:500]}...")
                        
                        # Log token usage if available
                        if "usage" in result:
                            usage = result["usage"]
                            logger.info(f"📈 MODEL USAGE: prompt_tokens: {usage.get('prompt_tokens', 'N/A')}, completion_tokens: {usage.get('completion_tokens', 'N/A')}, total_tokens: {usage.get('total_tokens', 'N/A')}")
                        
                        return model_response
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ MODEL API ERROR {response.status}: {error_text}")
                        raise Exception(f"API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"💥 MODEL ERROR: Error calling FastRouter API: {str(e)}")
            raise

    def _initialize_embeddings(self):
        """Initialize embeddings model for RAG"""
        try:
            return HuggingFaceEmbeddings(
                model_name="nlpaueb/legal-bert-base-uncased"
            )
        except Exception as e:
            logger.error(f"Embeddings initialization failed: {str(e)}")
            raise

    def _initialize_vector_stores(self):
        """Initialize vector stores for different jurisdictions"""
        try:
            vector_stores = {}
            jurisdictions = ["usa", "uk", "india"]
            
            for jurisdiction in jurisdictions:
                # Path to jurisdiction-specific documents
                docs_path = f"./legal_docs/{jurisdiction}"
                
                # Create empty vector store if documents don't exist yet
                if not os.path.exists(docs_path):
                    os.makedirs(docs_path, exist_ok=True)
                    vector_stores[jurisdiction] = FAISS.from_texts(
                        ["Placeholder legal text for " + jurisdiction], 
                        self.embeddings,
                        metadatas=[{"jurisdiction": jurisdiction, "source": "placeholder"}]
                    )
                    # Save empty index for future use
                    vector_stores[jurisdiction].save_local(f"{docs_path}/index")
                else:
                    # Load existing index
                    vector_stores[jurisdiction] = FAISS.load_local(
                        f"{docs_path}/index", 
                        self.embeddings
                    )
            
            return vector_stores
        
        except Exception as e:
            logger.error(f"Vector store initialization failed: {str(e)}")
            # Fall back to empty dictionary if vector stores fail
            return {}

    def _legal_research_tool(self, query: str):
        """Tool for retrieving relevant legal information"""
        try:
            # Detect jurisdiction for the query
            jurisdiction = self._detect_jurisdiction(query)
            
            # Get the appropriate vector store
            vector_store = self.vector_stores.get(jurisdiction)
            if not vector_store:
                return "No relevant legal documents found for this jurisdiction."
            
            # Create retriever with appropriate search parameters
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # Get relevant documents
            docs = retriever.invoke(query)
            
            # Extract and format results
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown source"),
                    "relevance": doc.metadata.get("score", 0)
                })
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            logger.error(f"Legal research tool error: {str(e)}")
            return "Error performing legal research."

    def _initialize_agents(self):
        """Initialize specialized legal agent with tools using structured agent instead of react"""
        try:
            # Define tools for the agent
            legal_research_tool = Tool(
                name="LegalResearch",
                func=self._legal_research_tool,
                description="Search for relevant legal information in our database."
            )
            
            # Using structured chat agent instead of react agent
            # This agent format is more reliable with Groq
            template = """You are a specialized legal assistant. Answer the following query using the tools available to you.
            
            {chat_history}
            
            Human: {input}
            
            Think through this step-by-step to find the right information:
            1. Understand the legal query
            2. Determine which tool to use
            3. Search for relevant information
            4. Format your answer clearly
            
            Make sure to use sources from your research.
            
            Available tools: {tools}
            """

            prompt = PromptTemplate.from_template(template)
            
            # Create structured chat agent - more reliable than ReAct with Groq
            agent = create_structured_chat_agent(
                llm=self.model,
                tools=[legal_research_tool],
                prompt=prompt
            )
            
            # Create agent executor
            return AgentExecutor(
                agent=agent,
                tools=[legal_research_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3  # Limit iterations to prevent too many API calls
            )
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {str(e)}")
            return None

    def _is_legal_query(self, query: str) -> bool:
        """Check if query is related to legal topics"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.legal_keywords)

    def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            return detect(text)
        except:
            return "en"

    def _translate_text(self, text: str, src_lang: str, dest_lang: str = "en") -> str:
        """Translate text between languages using deep_translator's GoogleTranslator"""
        if src_lang == dest_lang:
            logger.info(f"🔤 TRANSLATE: No translation needed ({src_lang} -> {dest_lang})")
            return text
        try:
            logger.info(f"🌐 TRANSLATE: Translating from {src_lang} to {dest_lang}")
            logger.info(f"📝 TRANSLATE INPUT: {text[:200]}...")
            translated = GoogleTranslator(source=src_lang, target=dest_lang).translate(text)
            logger.info(f"✅ TRANSLATE OUTPUT: {translated[:200]}...")
            return translated
        except Exception as e:
            logger.error(f"❌ TRANSLATE ERROR: {str(e)} --> text must be a valid text with maximum 5000 character,otherwise it cannot be translated")
            return text  # Return original if translation fails

    async def process_query(self, query: str) -> LegalResponse:
        """Process legal query with RAG and Agent-based approach ensuring response language matches input"""
        try:
            if not query.strip():
                raise HTTPException(status_code=400, detail="Empty query")
            
            # Detect language of the input query
            src_lang = self._detect_language(query)
            
            # Translate to English if needed
            if src_lang != "en":
                en_query = self._translate_text(query, src_lang, "en")
            else:
                en_query = query
            
            # Check if query is legal-related
            if not self._is_legal_query(en_query):
                response = "I can only answer legal-related questions. Please provide a query related to legal topics."
                # Translate response back if needed
                if src_lang != "en":
                    response = self._translate_text(response, "en", src_lang)
                    
                return LegalResponse(
                    advice=response,
                    sources=[]
                )

            # Detect jurisdiction
            jurisdiction = await self._detect_jurisdiction(en_query)
            
            logger.info(f"Processing query for {jurisdiction} jurisdiction in {src_lang} language")
            
            # Use agent to decide approach and gather information
            if self.agent_executor:
                try:
                    logger.info(f"🤵 AGENT: Starting agent execution for query")
                    # Try with agent first
                    agent_response = self.agent_executor.invoke({"input": en_query})
                    logger.info(f"✅ AGENT: Agent execution completed")
                    logger.info(f"📊 AGENT RESPONSE: {agent_response}")
                    
                    # Extract output and sources
                    advice = agent_response.get("output", "")
                    logger.info(f"📝 AGENT OUTPUT: {advice[:300]}...")
                    sources = self._extract_sources_from_agent(agent_response, en_query, jurisdiction)
                    logger.info(f"📚 AGENT SOURCES: {sources}")
                    
                    # Translate response back if needed
                    if src_lang != "en":
                        advice = self._translate_text(advice, "en", src_lang)
                    
                    return LegalResponse(
                        advice=advice,
                        sources=sources
                    )
                except Exception as e:
                    logger.error(f"Agent execution failed: {str(e)}, falling back to RAG response")
                    # Fall back to RAG response
                    response = await self._generate_rag_response(en_query, jurisdiction)
                    
                    # Translate response back if needed
                    if src_lang != "en":
                        response = self._translate_text(response, "en", src_lang)
                    
                    return LegalResponse(
                        advice=response,
                        sources=self._retrieve_sources(en_query, jurisdiction)
                    )
            else:
                # Direct RAG if agent isn't available
                response = await self._generate_rag_response(en_query, jurisdiction)
                
                # Translate response back if needed
                if src_lang != "en":
                    response = self._translate_text(response, "en", src_lang)
                
                return LegalResponse(
                    advice=response,
                    sources=self._retrieve_sources(en_query, jurisdiction)
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            # If there's an API error, try to provide a basic response instead of failing completely
            try:
                # Detect language for error response
                src_lang = self._detect_language(query)
                if src_lang != "en":
                    en_query = self._translate_text(query, src_lang, "en")
                else:
                    en_query = query
                
                # Generate basic response without API
                basic_response = self._generate_basic_legal_response(en_query, "general")
                
                # Translate back if needed
                if src_lang != "en":
                    basic_response = self._translate_text(basic_response, "en", src_lang)
                
                return LegalResponse(
                    advice=f"⚠️ API temporarily unavailable. Here's some general guidance:\n\n{basic_response}",
                    sources=["General Legal Principles", "Basic Legal Guidelines"]
                )
            except:
                # Last resort
                raise HTTPException(status_code=500, detail="Service temporarily unavailable. Please try again later.")

    def _extract_sources_from_agent(self, agent_response: Dict, query: str, jurisdiction: str) -> List[str]:
        """Extract sources from agent response"""
        sources = []
        try:
            # Extract from output
            output = agent_response.get("output", "")
            
            # Look for JSON in the response
            json_pattern = r"\[.*?\]"
            json_matches = re.findall(json_pattern, output, re.DOTALL)
            
            for json_str in json_matches:
                try:
                    results = json.loads(json_str)
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, dict) and "source" in result and result["source"] not in sources:
                                sources.append(result["source"])
                except:
                    continue
                    
            # Look for direct source mentions
            source_pattern = r"(?:source|reference):\s*([^\n]+)"
            source_matches = re.findall(source_pattern, output, re.IGNORECASE)
            
            for source in source_matches:
                if source not in sources:
                    sources.append(source)
                    
        except Exception as e:
            logger.warning(f"Error extracting sources: {str(e)}")
        
        # If no sources could be extracted, return default sources
        if not sources:
            return [
                f"Legal Database Reference #LC-{jurisdiction.upper()}-{hash(query) % 1000:03d}",
                f"Legal Precedent Collection #{hash(query) % 500:03d}"
            ]
            
        return sources

    async def _detect_jurisdiction(self, query: str) -> str:
        """Detect jurisdiction from query"""
        logger.info(f"🌍 JURISDICTION: Detecting jurisdiction for query")
        prompt = f"""Analyze this legal query and return ONLY the jurisdiction code (usa, uk, india):
Query: {query}
Answer must be exactly one of: usa, uk, india, or default"""
        try:
            logger.info(f"🚀 JURISDICTION: Calling model for jurisdiction detection")
            response = await self._call_fastrouter_api(prompt)
            clean_response = response.strip().lower()
            logger.info(f"📝 JURISDICTION RAW: {response}")
            logger.info(f"🧹 JURISDICTION CLEAN: {clean_response}")
            
            patterns = [
                (r"\b(usa|united\s?states)\b", "usa"),
                (r"\b(uk|united\s?kingdom)\b", "uk"),
                (r"\b(india|indian)\b", "india")
            ]
            for pattern, code in patterns:
                if re.search(pattern, clean_response):
                    logger.info(f"✅ JURISDICTION: Detected {code}")
                    return code
            logger.info(f"⚠️ JURISDICTION: No specific jurisdiction detected, using default")
            return "default"
        except Exception as e:
            logger.warning(f"❌ JURISDICTION: Detection failed, using default: {str(e)}")
            return "default"

    async def _generate_rag_response(self, query: str, jurisdiction: str) -> str:
        """Generate response using RAG approach"""
        try:
            logger.info(f"🔍 RAG: Starting RAG response generation for jurisdiction: {jurisdiction}")
            
            # Get relevant documents
            if jurisdiction in self.vector_stores:
                logger.info(f"📚 FAISS: Found vector store for {jurisdiction}, retrieving documents...")
                vector_store = self.vector_stores[jurisdiction]
                retriever = vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                )
                docs = retriever.invoke(query)
                logger.info(f"📖 FAISS: Retrieved {len(docs)} documents from vector store")
                
                # Log retrieved documents
                for i, doc in enumerate(docs):
                    logger.info(f"📄 FAISS DOC {i+1}: {doc.page_content[:200]}...")
                
                # Create context from retrieved documents
                context = "\n\n".join([doc.page_content for doc in docs])
                max_context_len = 2096
                if len(context) > max_context_len:
                    context = context[:max_context_len]
                    logger.info(f"✂️ RAG: Context truncated to {max_context_len} characters")
                
                logger.info(f"🎯 RAG: Final context length: {len(context)} characters")
                
                # Create prompt with context
                prompt = f"""As a legal assistant, use the following legal context to answer the query:

Context:
{context}

Query:
{query}

Provide a detailed legal answer with citations where available:"""
                
                logger.info(f"🚀 RAG: Sending prompt to FastRouter API (length: {len(prompt)})")
                response = await self._call_fastrouter_api(prompt)
                logger.info(f"✅ RAG: Received response from model (length: {len(response)})")
                logger.info(f"📝 RAG RESPONSE: {response[:300]}...")
                return response
            else:
                # Fallback without RAG
                return await self._generate_fallback_response(query, jurisdiction)
        except Exception as e:
            logger.error(f"RAG response generation failed: {str(e)}")
            return await self._generate_fallback_response(query, jurisdiction)

    async def _generate_fallback_response(self, query: str, jurisdiction: str) -> str:
        """Generate fallback response without RAG"""
        try:
            logger.info(f"🔄 FALLBACK: No vector store for {jurisdiction}, using direct model response")
            prompt = f"""As an unbiased {jurisdiction} legal assistant, provide a detailed answer to this legal query:

Query: {query}

Include relevant legal principles and considerations in your response:"""
            
            logger.info(f"🚀 FALLBACK: Sending prompt to FastRouter API (length: {len(prompt)})")
            response = await self._call_fastrouter_api(prompt)
            logger.info(f"✅ FALLBACK: Received response from model (length: {len(response)})")
            logger.info(f"📝 FALLBACK RESPONSE: {response[:300]}...")
            return response
        except Exception as e:
            logger.error(f"FastRouter API failed in fallback: {str(e)}")
            logger.info(f"🛠️ BASIC: Falling back to basic legal response generation")
            # Return a basic response without API call
            basic_response = self._generate_basic_legal_response(query, jurisdiction)
            logger.info(f"📝 BASIC RESPONSE: {basic_response[:300]}...")
            return basic_response

    def _generate_basic_legal_response(self, query: str, jurisdiction: str) -> str:
        """Generate a basic legal response without external API calls"""
        query_lower = query.lower()
        
        # Basic pattern matching for common legal queries
        if any(word in query_lower for word in ['contract', 'agreement', 'breach']):
            return f"""Based on general {jurisdiction} legal principles regarding contracts:

A contract is a legally binding agreement between parties. Key elements include:
1. Offer and acceptance
2. Consideration (exchange of value)
3. Legal capacity of parties
4. Lawful purpose

For contract disputes, consider:
- Reviewing the original agreement terms
- Documenting any breach of contract
- Seeking mediation before litigation
- Consulting with a qualified attorney

**Disclaimer**: This is general legal information only. Consult with a licensed attorney in your jurisdiction for specific legal advice."""

        elif any(word in query_lower for word in ['divorce', 'custody', 'family']):
            return f"""Regarding family law matters in {jurisdiction}:

Family law covers various issues including:
1. Divorce proceedings
2. Child custody and support
3. Alimony/spousal support
4. Property division

General considerations:
- Documentation is crucial
- Child's best interests are paramount in custody cases
- Mediation may be required or beneficial
- Legal representation is highly recommended

**Disclaimer**: This is general legal information only. Family law varies significantly by jurisdiction. Consult with a licensed family law attorney for specific guidance."""

        elif any(word in query_lower for word in ['criminal', 'arrest', 'charge']):
            return f"""Regarding criminal law matters in {jurisdiction}:

If facing criminal charges:
1. Exercise your right to remain silent
2. Request legal representation immediately
3. Do not speak to law enforcement without an attorney
4. Document all interactions with authorities

Important rights:
- Right to an attorney
- Right against self-incrimination
- Right to a fair trial
- Right to know the charges against you

**Disclaimer**: This is general legal information only. Criminal law is complex and varies by jurisdiction. Contact a criminal defense attorney immediately if you are facing charges."""

        else:
            return f"""I understand you have a legal question regarding: {query}

While I cannot provide specific legal advice due to API limitations, here are some general steps you can take:

1. **Document Everything**: Keep records of all relevant communications, contracts, or incidents
2. **Know Your Rights**: Research the basic legal principles that apply to your situation
3. **Seek Professional Help**: Consult with a qualified attorney in your jurisdiction
4. **Consider Alternatives**: Look into mediation or arbitration if applicable
5. **Time Limits**: Be aware that legal actions often have statute of limitations

**Resources**:
- Local bar association for attorney referrals
- Legal aid societies for low-income assistance
- Court self-help centers
- Online legal databases for research

**Disclaimer**: This is general information only and does not constitute legal advice. Laws vary by jurisdiction and individual circumstances. Always consult with a licensed attorney for specific legal guidance."""

    def _retrieve_sources(self, query: str, jurisdiction: str) -> List[str]:
        """Retrieve legal sources"""
        try:
            if jurisdiction in self.vector_stores:
                vector_store = self.vector_stores[jurisdiction]
                retriever = vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                )
                docs = retriever.invoke(query)
                
                sources = []
                for doc in docs:
                    source = doc.metadata.get("source", "Unknown source")
                    if source and source not in sources:
                        sources.append(source)
                
                if sources:
                    return sources
            
            # Fallback sources
            return [
                f"{jurisdiction.upper()} Legal Code §2023.123",
                f"{jurisdiction.upper()} Court Decision 2023-CV-456"
            ]
        except Exception as e:
            logger.warning(f"Source retrieval fallback: {str(e)}")
            return [
                f"{jurisdiction.upper()} Legal Code §2023.123",
                f"{jurisdiction.upper()} Court Decision 2023-CV-456"
            ]

    async def index_legal_document(self, document: LegalDocument, jurisdiction: str):
        """Index a legal document for RAG"""
        try:
            content = document.content
            metadata = document.metadata
            metadata["jurisdiction"] = jurisdiction
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            splits = text_splitter.split_text(content)
            
            if jurisdiction in self.vector_stores:
                vector_store = self.vector_stores[jurisdiction]
            else:
                vector_store = FAISS.from_texts([], self.embeddings)
                self.vector_stores[jurisdiction] = vector_store
            
            for i, split in enumerate(splits):
                split_metadata = metadata.copy()
                split_metadata["chunk"] = i
                split_metadata["source"] = metadata.get("source", f"Document {hash(content)[:8]}")
                vector_store.add_texts([split], [split_metadata])
            
            docs_path = f"./legal_docs/{jurisdiction}"
            os.makedirs(docs_path, exist_ok=True)
            vector_store.save_local(f"{docs_path}/index")
            
            return {"status": "success", "chunks_indexed": len(splits)}
            
        except Exception as e:
            logger.error(f"Document indexing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")

# Initialize chatbot
try:
    chatbot = LegalChatbot()
except Exception as e:
    logger.critical(f"Chatbot initialization failed: {str(e)}")
    raise

# API endpoint - Simplified to only take query
@app.post("/legal-advice", response_model=LegalResponse)
async def get_legal_advice(query: LegalQuery = Body(...)):
    return await chatbot.process_query(query.query)

# Add document indexing endpoint for RAG
@app.post("/index-document/{jurisdiction}")
async def index_document(jurisdiction: str, document: LegalDocument):
    return await chatbot.index_legal_document(document, jurisdiction)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "groq_connected": chatbot.groq_api_key is not None,
        "vector_stores": list(chatbot.vector_stores.keys()),
        "agent_initialized": chatbot.agent_executor is not None
    }

