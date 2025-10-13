// frontend/src/components/comments/CommentSection.jsx
import { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Loader } from 'lucide-react';
import api from '../../services/api';
import CommentItem from './CommentItem';
import CommentForm from './CommentForm';
import { logger } from '../../utils/logger';

function CommentSection({ clipId, videoRef = null }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  const fetchComments = useCallback(async (pageNum = 1, append = false) => {
    try {
      const response = await api.get(`/clips/${clipId}/comments`, {
        params: { page: pageNum, limit: 20 }
      });

      // Sprawdzanie czy response.data.comments istnieje, jeśli nie, używamy pustej tablicy
      const receivedComments = response.data?.comments || [];

      if (append) {
        setComments(prev => [...prev, ...receivedComments]);
      } else {
        setComments(receivedComments);
      }

      setTotal(response.data?.total || 0);
      setHasMore(response.data?.page < response.data?.pages);
    } catch (err) {
      logger.error('Failed to fetch comments:', err);
      // W przypadku błędu, ustaw pustą tablicę komentarzy jeśli nie jest to dołączanie
      if (!append) {
        setComments([]);
      }
    } finally {
      setLoading(false);
    }
  }, [clipId]);

  useEffect(() => {
    fetchComments(1, false);
  }, [fetchComments]);

  const handleCommentAdded = (newComment) => {
    setComments(prev => [newComment, ...prev]);
    setTotal(prev => prev + 1);
  };

  const handleReplyAdded = (parentId, newReply) => {
    setComments(prev => prev.map(comment => {
      if (comment.id === parentId) {
        return {
          ...comment,
          replies: [...(comment.replies || []), newReply],
          reply_count: comment.reply_count + 1
        };
      }
      return comment;
    }));
  };

  const handleCommentUpdated = (commentId, updatedContent) => {
    setComments(prev => prev.map(comment => {
      if (comment.id === commentId) {
        return { ...comment, content: updatedContent, is_edited: true };
      }
      if (comment.replies) {
        return {
          ...comment,
          replies: comment.replies.map(reply =>
            reply.id === commentId
              ? { ...reply, content: updatedContent, is_edited: true }
              : reply
          )
        };
      }
      return comment;
    }));
  };

  const handleCommentDeleted = (commentId, isReply, parentId) => {
    if (isReply && parentId) {
      setComments(prev => prev.map(comment => {
        if (comment.id === parentId) {
          return {
            ...comment,
            replies: comment.replies.filter(r => r.id !== commentId),
            reply_count: comment.reply_count - 1
          };
        }
        return comment;
      }));
    } else {
      setComments(prev => prev.filter(c => c.id !== commentId));
      setTotal(prev => prev - 1);
    }
  };

  const loadMoreComments = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchComments(nextPage, true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="animate-spin text-purple-500" size={32} />
      </div>
    );
  }

return (
    <div className="space-y-4">
      {/* Comment Form */}
      <CommentForm
        clipId={clipId}
        videoRef={videoRef}
        onCommentAdded={handleCommentAdded}
      />

      {/* Comments Header */}
      <div className="flex items-center gap-2 text-gray-400">
        <MessageSquare size={18} />
        <span className="text-sm font-medium">
          {total === 0 ? 'Brak komentarzy' : `${total} ${total === 1 ? 'komentarz' : total < 5 ? 'komentarze' : 'komentarzy'}`}
        </span>
      </div>

      {/* Comments List */}
      <div className="space-y-4">
        {comments.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <MessageSquare size={48} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">Dodaj pierwszy!</p>
          </div>
        ) : (
          comments.map(comment => (
            <CommentItem
              key={comment.id}
              comment={comment}
              clipId={clipId}
              videoRef={videoRef}
              onReplyAdded={handleReplyAdded}
              onCommentUpdated={handleCommentUpdated}
              onCommentDeleted={handleCommentDeleted}
            />
          ))
        )}
      </div>

      {/* Load More */}
      {hasMore && comments.length > 0 && (
        <button
          onClick={loadMoreComments}
          className="w-full py-3 text-purple-400 hover:text-purple-300 hover:bg-gray-800/50 rounded-lg text-sm font-medium transition"
        >
          Załaduj więcej komentarzy
        </button>
      )}
    </div>
  );
}

export default CommentSection;
