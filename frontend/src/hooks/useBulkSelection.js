import { useState, useCallback, useRef } from 'react';

/**
 * Hook do zarządzania bulk selection z obsługą Shift+Click
 *
 * Features:
 * - Toggle pojedynczych elementów
 * - Shift+Click do zaznaczania zakresu
 * - Select all / deselect all
 * - Clear selection
 */
export function useBulkSelection(items = []) {
  const [selectedIds, setSelectedIds] = useState(new Set());
  const lastClickedIndex = useRef(null);

  const toggleSelection = useCallback((id, index, isShiftPressed = false) => {
    setSelectedIds(prev => {
      const newSelection = new Set(prev);

      if (isShiftPressed && lastClickedIndex.current !== null) {
        // Shift+Click: zaznacz zakres
        const start = Math.min(lastClickedIndex.current, index);
        const end = Math.max(lastClickedIndex.current, index);

        for (let i = start; i <= end; i++) {
          if (items[i]) {
            newSelection.add(items[i].id);
          }
        }
      } else {
        // Normalny click: toggle
        if (newSelection.has(id)) {
          newSelection.delete(id);
        } else {
          newSelection.add(id);
        }
      }

      lastClickedIndex.current = index;
      return newSelection;
    });
  }, [items]);

  const selectAll = useCallback(() => {
    const allIds = new Set(items.map(item => item.id));
    setSelectedIds(allIds);
    lastClickedIndex.current = null;
  }, [items]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
    lastClickedIndex.current = null;
  }, []);

  const isSelected = useCallback((id) => {
    return selectedIds.has(id);
  }, [selectedIds]);

  return {
    selectedIds: Array.from(selectedIds),
    selectedCount: selectedIds.size,
    toggleSelection,
    selectAll,
    clearSelection,
    isSelected,
    hasSelection: selectedIds.size > 0,
  };
}
