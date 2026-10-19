import { Fragment } from 'react';

/** Renders `backtick` segments of a plain string as <code> elements. */
export default function formatInlineCode(text) {
  return text.split('`').map((part, index) =>
    index % 2 === 1 ? <code key={index}>{part}</code> : <Fragment key={index}>{part}</Fragment>,
  );
}
