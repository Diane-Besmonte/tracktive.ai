// Title Case with common rules (AP/Chicago-ish)
const SMALL_WORDS = new Set([
  "a","an","and","as","at","but","by","for","in","nor","of","on","or","per",
  "the","to","vs","via","with","from","over","into","onto","off","up","down"
]);

export function toTitleCase(input: string): string {
  if (!input) return "";
  // normalize separators to spaces for nicer titles
  const cleaned = input.replace(/[_]+/g, " ").replace(/\s+/g, " ").trim();

  // Split with word boundaries but preserve punctuation like : and -
  const parts = cleaned.split(/(\s+|[-–—:;])/);

  let firstWordIdx = -1, lastWordIdx = -1;
  // find indexes of first/last actual word tokens
  parts.forEach((p, i) => {
    if (/\w/.test(p) && !/^\s+$/.test(p) && !/^[-–—:;]$/.test(p)) {
      if (firstWordIdx === -1) firstWordIdx = i;
      lastWordIdx = i;
    }
  });

  let afterPunct = true; // capitalize word right after colon/dash
  return parts
    .map((token, i) => {
      if (/^\s+$/.test(token) || /^[-–—:;]$/.test(token)) {
        afterPunct = /^[-–—:]$/.test(token); // only colon/dash force cap next
        return token;
      }

      const w = token;

      // keep ALL-CAPS acronyms (2+ letters) as-is: API, RAG, LLM, SQL
      if (/^[A-Z]{2,}$/.test(w)) { afterPunct = false; return w; }

      const lower = w.toLowerCase();

      const isWord = /\w/.test(w);
      const isFirst = i === firstWordIdx;
      const isLast = i === lastWordIdx;

      if (isWord) {
        if (afterPunct || isFirst || isLast || !SMALL_WORDS.has(lower)) {
          // capitalize first letter, keep the rest lower (preserve apostrophes)
          const capped = lower
            .replace(/^([a-z])/, (m) => m.toUpperCase())
            .replace(/(^|\W)([a-z])/g, (...args: string[]) => args[1] + args[2].toUpperCase());
          afterPunct = false;
          return capped;
        } else {
          afterPunct = false;
          return lower;
        }
      }

      afterPunct = false;
      return w;
    })
    .join("");
}
