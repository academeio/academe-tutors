import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function StreamingMessage({ content }: { content: string }) {
  return (
    <div className="prose prose-sm prose-slate max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      <span className="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-0.5" />
    </div>
  );
}
