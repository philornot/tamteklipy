// frontend/src/components/comments/CommentSection.jsx
import { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Loader } from 'lucide-react';
import api from '../../services/api';
import CommentItem from './CommentItem';
import CommentForm from './CommentForm';

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
      console.error('Failed to fetch comments:', err);
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 pb-4 border-b border-gray-700">
        <MessageSquare size={20} className="text-purple-400" />
        <h3 className="text-lg font-semibold">
          Komentarze {total > 0 && `(${total})`}
        </h3>
      </div>

      {/* Comment Form */}
      <CommentForm
        clipId={clipId}
        videoRef={videoRef}
        onCommentAdded={handleCommentAdded}
      />

      {/* Comments List */}
      <div className="space-y-4">
        {comments.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <MessageSquare size={48} className="mx-auto mb-2 opacity-50" />
            <p>Brak komentarzy. Bądź pierwszy!</p>
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
          className="w-full py-2 text-purple-400 hover:text-purple-300 text-sm font-medium transition"
        >
          Załaduj więcej komentarzy
        </button>
      )}
    </div>
  );
}

export default CommentSection;
