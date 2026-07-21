export function StatusLine({ data, L }) {
  const s = data?.stats;
  return (
    <div className="py-3.5 font-mono text-xs text-text-tertiary">
      {s ? (
        <>
          {L.st.source} <b className="font-semibold text-text-secondary">{data.offline ? L.st.sample : data.repo}</b>
          {"  "}{L.st.backend} <b className="font-semibold text-text-secondary">{data.backend}</b>
          {"  "}{L.st.llm} <b className="font-semibold text-text-secondary">{data.llm}</b>
          {"  "}{L.st.run} <b className="font-semibold text-text-secondary">{data.run_id}</b>
          {"  "}{data.count} {L.st.items}
        </>
      ) : (
        "\u00a0"
      )}
    </div>
  );
}
