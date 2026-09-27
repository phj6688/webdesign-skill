// fixture-expect undersized-ui-text count=0
export function Actions({ onCopy, onShare }) {
  return (
    <div className="flex gap-2">
      <span onClick={onCopy} className="text-[11.5px]">Copy the link to this page</span>
      <span role="button" onKeyDown={onShare} className="text-[11px]">Share with the team</span>
    </div>
  );
}
