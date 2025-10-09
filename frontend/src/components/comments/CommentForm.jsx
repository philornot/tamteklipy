// frontend/src/components/comments/CommentForm.jsx
import { useState, useRef, useEffect } from 'react';
import { Send, Clock, X } from 'lucide-react';
import api from '../../services/api';
import MentionAutocomplete from './MentionAutocomplete';

function CommentForm({
  clipId,
  videoRef = null,
  parentId = null,
  onCommentAdded,
  onCancel = null,
  placeholder = "Napisz komentarz..."
}) {
  const [content, setContent] = useState('');
  const [timestamp, setTimestamp] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionPosition, setMentionPosition] = useState(0);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [content]);

  // Detect @mentions
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = content.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);

      // Check if there's a space after @
      if (!textAfterAt.includes(' ') && textAfterAt.length > 0) {
        setShowMentions(true);
        setMentionQuery(textAfterAt);
        setMentionPosition(lastAtIndex);
      } else {
        setShowMentions(false);
      }
    } else {
      setShowMentions(false);
    }
  }, [content]);

  const handleSubmit = async (e) => {
  e.preventDefault();

  if (!content.trim()) {
    setError('Komentarz nie może być pusty');
    return;
  }

  if (content.length > 1000) {
    setError('Komentarz nie może przekraczać 1000 znaków');
    return;
  }

  setSubmitting(true);
  setError(null);

  try {
    const response = await api.post(`/clips/${clipId}/comments`, {
      content: content.trim(),
      timestamp: timestamp,
      parent_id: parentId
    });

    setContent('');
    setTimestamp(null);
    onCommentAdded(response.data);

    if (onCancel) {
      onCancel();
    }
  } catch (err) {
    console.error('Failed to post comment:', err);
    setError(err.response?.data?.message || 'Nie udało się dodać komentarza');
  } finally {
    setSubmitting(false);
  }
};

  const captureTimestamp = () => {
    if (videoRef?.current) {
      const currentTime = Math.floor(videoRef.current.currentTime);
      setTimestamp(currentTime);
    }
  };

  const removeTimestamp = () => {
    setTimestamp(null);
  };

  const handleMentionSelect = (username) => {
    const beforeMention = content.substring(0, mentionPosition);
    const afterMention = content.substring(mentionPosition + mentionQuery.length + 1);

    setContent(`${beforeMention}@${username} ${afterMention}`);
    setShowMentions(false);
    textareaRef.current?.focus();
  };

  const formatTimestamp = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Textarea */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={placeholder}
          disabled={submitting}
          className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 min-h-[80px] max-h-[300px]"
          maxLength={1000}
        />

        {/* Mention Autocomplete */}
        {/* todo: napraw autocomplete i mnie odkomentuj */}
        {/*{showMentions && (*/}
        {/*  <MentionAutocomplete*/}
        {/*    query={mentionQuery}*/}
        {/*    onSelect={handleMentionSelect}*/}
        {/*    onClose={() => setShowMentions(false)}*/}
        {/*  />*/}
        {/*)}*/}
      </div>

      {/* Character counter */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-4">
          {/* Timestamp badge */}
          {timestamp !== null && (
            <div className="flex items-center gap-2 bg-purple-900/30 px-3 py-1 rounded-full border border-purple-500/30">
              <Clock size={14} className="text-purple-400" />
              <span className="text-purple-300">{formatTimestamp(timestamp)}</span>
              <button
                type="button"
                onClick={removeTimestamp}
                className="text-purple-400 hover:text-purple-300"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </div>

        <span className={content.length > 900 ? 'text-yellow-400' : ''}>
          {content.length}/1000
        </span>
      </div>

      {/* Error */}
      {error && (
        <div className="text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Timestamp button (tylko dla video) */}
        {videoRef && !parentId && (
          <button
            type="button"
            onClick={captureTimestamp}
            disabled={submitting}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-50"
          >
            <Clock size={16} />
            <span className="text-sm">Dodaj timestamp</span>
          </button>
        )}

        {/* Cancel button (dla replies) */}
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-4 py-2 text-gray-400 hover:text-white transition disabled:opacity-50"
          >
            Anuluj
          </button>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={submitting || !content.trim()}
          className="ml-auto flex items-center gap-2 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Wysyłanie...
            </>
          ) : (
            <>
              <Send size={16} />
              Wyślij
            </>
          )}
        </button>
      </div>
    </form>
  );
}

export default CommentForm;

