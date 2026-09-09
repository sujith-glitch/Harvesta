function cleanInlineMarkers(value) {
  return value
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .trim();
}

/** Convert safe plain-text model output into phone-friendly display blocks. */
export function formatChatReply(content) {
  const lines = String(content || '').replace(/\r\n/g, '\n').split('\n');

  return lines.map((rawLine, index) => {
    const line = rawLine.trim();
    if (!line) return { type: 'spacer', text: '', key: index };

    const bullet = line.match(/^[-*•]\s+(.+)$/);
    if (bullet) return { type: 'bullet', text: cleanInlineMarkers(bullet[1]), marker: '•', key: index };

    const numbered = line.match(/^(\d+)[.)]\s+(.+)$/);
    if (numbered) {
      return {
        type: 'bullet',
        text: cleanInlineMarkers(numbered[2]),
        marker: `${numbered[1]}.`,
        key: index,
      };
    }

    const markdownHeading = line.match(/^#{1,6}\s+(.+)$/) || line.match(/^\*\*(.+)\*\*:?$/);
    const followsBreak = index === 0 || !lines[index - 1].trim();
    const plainHeading = followsBreak && line.length <= 58 && !/[.!?;:]$/.test(line);
    if (markdownHeading || plainHeading) {
      return {
        type: 'heading',
        text: cleanInlineMarkers(markdownHeading ? markdownHeading[1] : line),
        key: index,
      };
    }

    return { type: 'paragraph', text: cleanInlineMarkers(line), key: index };
  });
}
