import Icon from './Icon';
import cx from '../../utils/classNames';
import { copyToClipboard, notify } from '../../utils/notify';

/** Copies `text` to the clipboard and shows `message`. `bare` drops the padded hover background. */
export default function CopyButton({ text, message, title = 'Copy URL', iconSize = 'xs', bare = false, stopPropagation = false }) {
  const handleClick = async (event) => {
    if (stopPropagation) event.stopPropagation();
    await copyToClipboard(text);
    notify(message);
  };

  return (
    <button
      type="button"
      className={cx('icon-btn', bare && 'icon-btn--bare')}
      onClick={handleClick}
      title={title}
      aria-label={title}
    >
      <Icon name="content_copy" size={iconSize} />
    </button>
  );
}
