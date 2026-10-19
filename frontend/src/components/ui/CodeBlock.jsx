import cx from '../../utils/classNames';

/** Read-only dark terminal-style code block. */
export default function CodeBlock({ code, className }) {
  return (
    <div className={cx('terminal', 'code-block', 'dark-scroll', className)}>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}
