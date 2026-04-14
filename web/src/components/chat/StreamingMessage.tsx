export function StreamingMessage({ content }: { content: string }) {
  return (
    <div className="whitespace-pre-wrap">
      {content}
      <span className="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-0.5" />
    </div>
  );
}
