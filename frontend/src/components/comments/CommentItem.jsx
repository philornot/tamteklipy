// frontend/src/components/comments/CommentItem.jsx
import { useState } from 'react';
import { Edit2, Trash2, Reply, Clock, Shield } from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import CommentForm from './CommentForm';
import { logger } from '../../utils/logger';

function CommentItem({
  comment,
  clipId,
  videoRef = null,
  onReplyAdded,
  onCommentUpdated,
  onCommentDeleted,
  isReply = false
}) {
  const { user } = useAuth();
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isOwner = user?.id === comment.user_id;
  const canEdit = isOwner && comment.can_edit;
  const canDelete = isOwner || user?.is_admin;

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'teraz';
    if (diffMins < 60) return `${diffMins}min temu`;
    if (diffHours < 24) return `${diffHours}h temu`;
    if (diffDays === 1) return 'wczoraj';
    if (diffDays < 7) return `${diffDays} dni temu`;

    return date.toLocaleDateString('pl-PL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatTimestamp = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const handleTimestampClick = () => {
    if (videoRef?.current && comment.timestamp !== null) {
      videoRef.current.currentTime = comment.timestamp;
      videoRef.current.play();
    }
  };

  const handleEdit = async () => {
    if (!editContent.trim() || editContent === comment.content) {
      setIsEditing(false);
      return;
    }

    setUpdating(true);
    try {
      await api.put(`/comments/${comment.id}`, {
        content: editContent.trim()
      });

      onCommentUpdated(comment.id, editContent.trim());
      setIsEditing(false);
    } catch (err) {
      logger.error('Failed to update comment:', err);
      alert(err.response?.data?.message || 'Nie udało się zaktualizować komentarza');
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Czy na pewno chcesz usunąć ten komentarz?')) {
      return;
    }

    setDeleting(true);
    try {
      await api.delete(`/comments/${comment.id}`);
      onCommentDeleted(comment.id, isReply, comment.parent_id);
    } catch (err) {
      logger.error('Failed to delete comment:', err);
      alert(err.response?.data?.message || 'Nie udało się usunąć komentarza');
    } finally {
      setDeleting(false);
    }
  };

  const renderContent = () => {
    if (isEditing) {
      return (
        <div className="space-y-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            disabled={updating}
            className="w-full bg-gray-700 text-white rounded px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 min-h-[80px]"
            maxLength={1000}
          />
          <div className="flex items-center gap-2">
            <button
              onClick={handleEdit}
              disabled={updating || !editContent.trim()}
              className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm font-medium transition disabled:opacity-50"
            >
              {updating ? 'Zapisywanie...' : 'Zapisz'}
            </button>
            <button
              onClick={() => {
                setIsEditing(false);
                setEditContent(comment.content);
              }}
              disabled={updating}
              className="px-3 py-1 text-gray-400 hover:text-white transition disabled:opacity-50 text-sm"
            >
              Anuluj
            </button>
            <span className="text-xs text-gray-500 ml-auto">
              {editContent.length}/1000
            </span>
          </div>
        </div>
      );
    }

    // Render HTML content with mentions
    return (
      <div
        className="text-gray-200"
        dangerouslySetInnerHTML={{ __html: comment.content_html }}
      />
    );
  };

  return (
    <div className={`${isReply ? 'ml-8 pl-4 border-l-2 border-gray-700' : ''}`}>
      <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          {/* Avatar placeholder */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-sm">
            {comment.user.username[0].toUpperCase()}
          </div>

          {/* User info */}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">
                {comment.user.username}
              </span>
              {comment.user.is_admin && (
                <Shield size={14} className="text-purple-400" title="Admin" />
              )}
              <span className="text-gray-500 text-sm">·</span>
              <span className="text-gray-500 text-sm">
                {formatTimeAgo(comment.created_at)}
              </span>
              {comment.is_edited && (
                <>
                  <span className="text-gray-500 text-sm">·</span>
                  <span className="text-gray-500 text-xs italic">
                    edytowany
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div>{renderContent()}</div>

        {/* Timestamp badge */}
        {comment.timestamp !== null && videoRef && (
          <button
            onClick={handleTimestampClick}
            className="flex items-center gap-1 px-2 py-1 bg-purple-900/30 hover:bg-purple-900/50 rounded text-purple-300 text-xs transition"
          >
            <Clock size={12} />
            <span>{formatTimestamp(comment.timestamp)}</span>
          </button>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4 text-sm">
          {/* Reply button */}
          {!isReply && (
            <button
              onClick={() => setShowReplyForm(!showReplyForm)}
              className="flex items-center gap-1 text-gray-400 hover:text-purple-400 transition"
            >
              <Reply size={14} />
              <span>Odpowiedz</span>
              {comment.reply_count > 0 && (
                <span className="text-xs">({comment.reply_count})</span>
              )}
            </button>
          )}

          {/* Edit button */}
          {canEdit && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1 text-gray-400 hover:text-blue-400 transition"
            >
              <Edit2 size={14} />
              <span>Edytuj</span>
            </button>
          )}

          {/* Delete button */}
          {canDelete && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition disabled:opacity-50"
            >
              <Trash2 size={14} />
              <span>{deleting ? 'Usuwanie...' : 'Usuń'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Reply Form */}
      {showReplyForm && !isReply && (
        <div className="mt-3 ml-8">
          <CommentForm
            clipId={clipId}
            videoRef={videoRef}
            parentId={comment.id}
            onCommentAdded={(newReply) => {
              onReplyAdded(comment.id, newReply);
              setShowReplyForm(false);
            }}
            onCancel={() => setShowReplyForm(false)}
            placeholder="Napisz odpowiedź..."
          />
        </div>
      )}

      {/* Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3 space-y-3">
          {comment.replies.map(reply => (
            <CommentItem
              key={reply.id}
              comment={reply}
              clipId={clipId}
              videoRef={videoRef}
              onCommentUpdated={onCommentUpdated}
              onCommentDeleted={onCommentDeleted}
              isReply={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default CommentItem;