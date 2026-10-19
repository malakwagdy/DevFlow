import { Fragment } from 'react';

/** Renders a list of pipeline stages separated by "→" arrows. */
export default function StageFlow({ items, renderItem, getKey = (_, index) => index }) {
  return items.map((item, index) => (
    <Fragment key={getKey(item, index)}>
      {index > 0 && (
        <span className="flow-arrow" aria-hidden="true">
          →
        </span>
      )}
      {renderItem(item, index)}
    </Fragment>
  ));
}
