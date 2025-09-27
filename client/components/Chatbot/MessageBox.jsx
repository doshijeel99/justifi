import React, { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Logo } from "@/public/images";
import {
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  Scale,
  FileText,
} from "lucide-react";

const MessageBox = ({ message, messageId }) => {
  const [feedbackType, setFeedbackType] = useState(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleFeedbackSubmit = (type) => {
    // Here you would typically send the feedback to your backend
    console.log({
      messageId,
      feedbackType: type,
      timestamp: new Date().toISOString(),
    });

    setFeedbackType(type);
    setFeedbackSubmitted(true);

    // Reset after delay if needed
    // setTimeout(() => {
    //   setFeedbackSubmitted(false);
    //   setFeedbackType(null);
    // }, 5000);
  };

  const feedbackOptions = [
    {
      id: "helpful",
      icon: <ThumbsUp className="w-4 h-4" />,
      label: "Helpful",
      color: "bg-green-100 hover:bg-green-200 text-green-700 border-green-200",
    },
    {
      id: "not_helpful",
      icon: <ThumbsDown className="w-4 h-4" />,
      label: "Not Helpful",
      color: "bg-red-100 hover:bg-red-200 text-red-700 border-red-200",
    },
    {
      id: "confusing",
      icon: <MessageSquare className="w-4 h-4" />,
      label: "Confusing",
      color:
        "bg-yellow-100 hover:bg-yellow-200 text-yellow-700 border-yellow-200",
    },
    {
      id: "incorrect",
      icon: <AlertTriangle className="w-4 h-4" />,
      label: "Incorrect",
      color:
        "bg-orange-100 hover:bg-orange-200 text-orange-700 border-orange-200",
    },
  ];

  const formatMessage = (text) => {
    if (!text) return null;

    // Check if the message is an object with advice and sources properties
    if (typeof text === "object" && text !== null) {
      // If message is an object, handle it appropriately
      if (text.advice && text.sources) {
        return (
          <div>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="font-bold text-lg text-limeGreen-900 leading-relaxed whitespace-pre-line tracking-wide transition-colors duration-300 p-2 rounded-lg hover:bg-blue-500/5"
            >
              {text.advice}
            </motion.p>
            {text.sources && (
              <div className="mt-4 text-sm text-gray-600">
                <h4 className="font-medium mb-2">Sources:</h4>
                <ul className="list-disc pl-5">
                  {Array.isArray(text.sources) ? (
                    text.sources.map((source, idx) => (
                      <li key={idx}>{source}</li>
                    ))
                  ) : (
                    <li>{String(text.sources)}</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        );
      }

      // If it's another type of object, convert it to string
      return (
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-bold text-lg text-limeGreen-900 leading-relaxed whitespace-pre-line tracking-wide hover:text-white transition-colors duration-300 p-2 rounded-lg hover:bg-blue-500/5"
        >
          {JSON.stringify(text, null, 2)}
        </motion.p>
      );
    }

    // Handle string message
    return (
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="font-bold text-lg text-limeGreen-900 leading-relaxed whitespace-pre-line tracking-wide hover:text-white transition-colors duration-300 p-2 rounded-lg hover:bg-blue-500/5"
      >
        {text}
      </motion.p>
    );
  };

  const formatLegalContent = (text) => {
    // Split by sections which are indicated by **Section Title:**
    const sections = text.split(/\*\*([^*]+)\*\*/).filter(Boolean);

    // Find sources if they exist
    const sourcesMatch = text.match(
      /sources\s*:\s*Array\((\d+)\)([\s\S]*?)(?=\s*$)/
    );
    const sourcesList = sourcesMatch ? parseSources(sourcesMatch[2]) : [];

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="space-y-4"
      >
        {/* Disclaimer Banner */}
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md"
        >
          <div className="flex items-center gap-2">
            <Scale className="text-blue-600 w-5 h-5" />
            <p className="text-blue-800 font-medium">Legal Information</p>
          </div>
          <p className="text-sm text-blue-700 mt-1">
            This is general information only and not legal advice. Consult with
            a licensed attorney for advice specific to your situation.
          </p>
        </motion.div>

        {/* Content sections */}
        <div className="space-y-6">
          {sections.map((section, index) => {
            // If it's a section title (odd indices in our split array)
            if (index % 2 === 0) {
              const sectionTitle = sections[index - 1];
              const content = processLegalContent(section);

              if (!sectionTitle) return null;

              return (
                <motion.div
                  key={index}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="border border-gray-200 rounded-lg overflow-hidden"
                >
                  <div className="flex items-center gap-2 bg-gray-100 px-4 py-3 border-b border-gray-200">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <h3 className="font-semibold text-gray-800">
                      {sectionTitle}
                    </h3>
                  </div>
                  <div className="p-4 bg-white">{content}</div>
                </motion.div>
              );
            }
            return null;
          })}
        </div>

        {/* Sources */}
        {sourcesList.length > 0 && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-6 pt-4 border-t border-gray-200"
          >
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-4 h-4 text-gray-600" />
              <h4 className="font-medium text-gray-700">Sources</h4>
            </div>
            <ul className="space-y-1">
              {sourcesList.map((source, idx) => (
                <li
                  key={idx}
                  className="text-sm text-gray-600 flex items-center gap-1"
                >
                  <Badge variant="outline" className="text-xs">
                    {idx + 1}
                  </Badge>
                  {source}
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </motion.div>
    );
  };

  const processLegalContent = (content) => {
    // Process bullet points
    const bulletPointRegex = /\*\s(.+?)(?=\n\*|\n\d|\n\n|$)/gs;
    content = content.replace(bulletPointRegex, (match, p1) => {
      return `<li class="ml-5 mt-2 flex items-start gap-2"><span class="text-blue-500 inline-block mt-1">•</span><span>${p1.trim()}</span></li>`;
    });

    // Process numbered lists - match digits followed by period, then text
    const numberedListRegex = /(\d+)\.\s(.+?)(?=\n\*|\n\d|\n\n|$)/gs;
    content = content.replace(numberedListRegex, (match, number, text) => {
      return `<li class="ml-5 mt-2 flex items-start gap-2"><span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full inline-block">${number}</span><span>${text.trim()}</span></li>`;
    });

    // Wrap lists in <ul> tags
    content = content.replace(
      /<li class="ml-5 mt-2 flex items-start gap-2">[\s\S]+?<\/li>/g,
      (match) => {
        return `<ul class="my-3 space-y-1">${match}</ul>`;
      }
    );

    // Process paragraphs (text that isn't a list item)
    const paragraphs = content.split("\n\n").filter(Boolean);
    const processedParagraphs = paragraphs.map((para) => {
      if (!para.includes('<li class="ml-5')) {
        return `<p class="my-3 text-gray-700 leading-relaxed">${para.trim()}</p>`;
      }
      return para;
    });

    return (
      <div dangerouslySetInnerHTML={{ __html: processedParagraphs.join("") }} />
    );
  };

  const parseSources = (sourcesText) => {
    // Extract sources from the text
    const sourceLines = sourcesText
      .split("\n")
      .filter((line) => line.includes(":"));
    return sourceLines.map((line) => {
      const parts = line.split(":");
      if (parts.length >= 2) {
        return parts[1].replace(/^[\s"]+|[\s"]+$/g, "");
      }
      return line.trim();
    });
  };

  const renderFeedbackUI = () => {
    if (feedbackSubmitted) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center py-3 mt-4 bg-green-50 rounded-lg border border-green-200"
        >
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">Thank you for your feedback!</span>
          </div>
        </motion.div>
      );
    }

    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-6 border-t border-gray-200 pt-4"
      >
        <div className="text-sm text-gray-500 mb-2">
          Was this response helpful?
        </div>
        <div className="flex flex-wrap gap-2">
          {feedbackOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => handleFeedbackSubmit(option.id)}
              className={`${option.color} px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 transition-all duration-200 border`}
            >
              {option.icon}
              {option.label}
            </button>
          ))}
        </div>
      </motion.div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="z-10 h-[500px] w-[900px]"
    >
      <Card className="h-full bg-gradient-to-tr from-white via-white/70 to-white/70 backdrop-blur-md border-white/10">
        {message === "" ? (
          <div className="h-full w-full flex justify-center items-center">
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                repeatType: "reverse",
              }}
            >
              <Image src={Logo} alt="amigo.ai" className="h-56 w-auto" />
            </motion.div>
          </div>
        ) : (
          <ScrollArea className="h-full w-full p-6 rounded-lg">
            <div>
              {formatMessage(message)}
              {message && renderFeedbackUI()}
            </div>
          </ScrollArea>
        )}
      </Card>
    </motion.div>
  );
};

export default MessageBox;
