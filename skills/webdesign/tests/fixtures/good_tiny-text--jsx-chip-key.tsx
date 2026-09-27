// fixture-expect undersized-ui-text count=0
export function Tags({ tags }) {
  return (
    <div className="flex gap-2">
      {tags.map((tag) => (
        <span
          key={tag}
          className="px-2 py-1 text-[10px] font-mono"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}
