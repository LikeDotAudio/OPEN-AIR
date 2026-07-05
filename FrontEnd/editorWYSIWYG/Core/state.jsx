/**
 * Header: state.jsx
 * Purpose: state component or utility.
 * Description: Handles logic and rendering for state component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Core/state.jsx — Central State Engine for the HTML5 WYSIWYG editor.
 *
 * Mirrors oaGuiEditorWYSIWYG/Core/state.py (StateManager). Holds the master
 * JSON for ONE GUI definition file ({ rootKey: OcaBin }), the current selection,
 * and the dirty flag. All mutations go through path-based ops and broadcast to
 * subscribers (publish/subscribe, the web equivalent of the STATE_UPDATED event).
 *
 * Paths are dot-strings into the full file object, e.g.
 *   "Spectrum_Instrument_bandwidth"
 *   "Spectrum_Instrument_bandwidth.blocks.Resolution Bandwidth"
 *   "Spectrum_Instrument_bandwidth.blocks.Resolution Bandwidth.fields.RBW"
 * GUI keys never contain '.', so dot-splitting is safe.
 */
(function () {
  const deepClone = (obj) =>
    (typeof structuredClone === 'function')
      ? structuredClone(obj)
      : JSON.parse(JSON.stringify(obj));

  const splitPath = (path) => (path ? String(path).split('.') : []);

  const getAtPath = (root, path) => {
    let node = root;
    for (const key of splitPath(path)) {
      if (node == null || typeof node !== 'object') return undefined;
      node = node[key];
    }
    return node;
  };

  // Set value in-place (root is expected to be a fresh clone owned by caller).
  const setAtPath = (root, path, value) => {
    const parts = splitPath(path);
    if (parts.length === 0) return;
    let node = root;
    for (let i = 0; i < parts.length - 1; i++) {
      if (node[parts[i]] == null || typeof node[parts[i]] !== 'object') node[parts[i]] = {};
      node = node[parts[i]];
    }
    node[parts[parts.length - 1]] = value;
  };

  const deleteAtPath = (root, path) => {
    const parts = splitPath(path);
    if (parts.length === 0) return;
    const parent = getAtPath(root, parts.slice(0, -1).join('.'));
    if (parent && typeof parent === 'object') delete parent[parts[parts.length - 1]];
  };

  // The dict that directly holds `path` (its parent container) and the last key.
  const containerOf = (root, path) => {
    const parts = splitPath(path);
    return {
      containerPath: parts.slice(0, -1).join('.'),
      container: getAtPath(root, parts.slice(0, -1).join('.')),
      key: parts[parts.length - 1],
    };
  };

  // Rebuild a dict preserving order but with `key` re-inserted at `index`.
  const reinsertKey = (dict, key, index) => {
    const entries = Object.entries(dict).filter(([k]) => k !== key);
    entries.splice(index, 0, [key, dict[key]]);
    const out = {};
    for (const [k, v] of entries) out[k] = v;
    return out;
  };

  const genUniqueKey = (container, base) => {
    const safeBase = base || 'element';
    if (!container || container[safeBase] === undefined) return safeBase;
    let i = 2;
    while (container[`${safeBase}_${i}`] !== undefined) i++;
    return `${safeBase}_${i}`;
  };

  // Which child-collection key does a container node use for its children?
  // OcaBin/OcaNotebook hold "blocks"; OcaBlock holds "fields".
  const childCollectionKey = (node) => {
    if (!node || typeof node !== 'object') return null;
    if (node.type === 'OcaBlock') return 'fields';
    if (node.blocks || node.type === 'OcaBin' || node.type === 'OcaNotebook') return 'blocks';
    if (node.fields) return 'fields';
    return 'fields';
  };

  window.OaEdState = {
    deepClone, splitPath, getAtPath, setAtPath, deleteAtPath, containerOf, genUniqueKey, childCollectionKey,

    /** Create a fresh editor store for a file. */
    create(initialData, filePath) {
      let state = {
        data: deepClone(initialData || {}),
        filePath: filePath || null,
        selectedPath: null,
        // Editable draft of a Library palette item the user clicked (NOT yet on the
        // canvas). When set, the Properties panel shows it + an "Add to Canvas" drag
        // handle. Picking a canvas node clears it. { name, schema } | null.
        libraryItem: null,
        dirty: false,
        rev: 0,
      };
      const listeners = new Set();
      const notify = () => {
        state = { ...state, rev: state.rev + 1 };
        listeners.forEach((fn) => fn(state));
      };

      const commit = (newData, { dirty = true } = {}) => {
        state = { ...state, data: newData, dirty: state.dirty || dirty };
        notify();
      };

      const api = {
        getState: () => state,
        subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },

        getData: () => state.data,
        getNode: (path) => getAtPath(state.data, path),
        getSelected: () => (state.selectedPath ? getAtPath(state.data, state.selectedPath) : null),

        select(path) { state = { ...state, selectedPath: path, libraryItem: null }; notify(); },

        // --- Library draft (palette item shown in Properties before it's placed) ---
        getLibraryItem: () => state.libraryItem,
        selectLibraryItem(comp) {
          state = {
            ...state,
            selectedPath: null,
            libraryItem: comp ? { name: comp.name, schema: deepClone(comp.schema) } : null,
          };
          notify();
        },
        clearLibraryItem() { state = { ...state, libraryItem: null }; notify(); },
        /** Edit a property on the library draft (dot key path into its schema). */
        setLibraryProp(key, value) {
          if (!state.libraryItem) return;
          const schema = deepClone(state.libraryItem.schema);
          setAtPath(schema, key, value);
          state = { ...state, libraryItem: { ...state.libraryItem, schema } };
          notify();
        },

        /** Replace the whole document (e.g. from the JSON code pane). */
        replaceData(data, opts) { commit(deepClone(data), opts); },

        /** Replace the node at `path` wholesale. */
        setNode(path, value) {
          const d = deepClone(state.data);
          setAtPath(d, path, value);
          commit(d);
        },

        /** Set a single property `key` on the node at `path` (dot key supported). */
        setProp(path, key, value) {
          const d = deepClone(state.data);
          setAtPath(d, path ? `${path}.${key}` : key, value);
          commit(d);
        },

        deleteNode(path) {
          const d = deepClone(state.data);
          deleteAtPath(d, path);
          commit(d);
          if (state.selectedPath === path) api.select(null);
        },

        /** Rename the last segment of `path` to `newKey` (keeps sibling order). */
        rename(path, newKey) {
          const d = deepClone(state.data);
          const { containerPath, container, key } = containerOf(d, path);
          if (!container || key === newKey || container[newKey] !== undefined) return;
          const idx = Object.keys(container).indexOf(key);
          container[newKey] = container[key];
          delete container[key];
          const reordered = reinsertKey(container, newKey, idx);
          setAtPath(d, containerPath, reordered);
          commit(d);
          const newPath = containerPath ? `${containerPath}.${newKey}` : newKey;
          state = { ...state, selectedPath: state.selectedPath === path ? newPath : state.selectedPath };
          notify();
        },

        /** Move element up/down (dir = -1 | +1) within its sibling collection. */
        reorder(path, dir) {
          const d = deepClone(state.data);
          const { containerPath, container, key } = containerOf(d, path);
          if (!container) return;
          const keys = Object.keys(container);
          const idx = keys.indexOf(key);
          const target = idx + dir;
          if (idx < 0 || target < 0 || target >= keys.length) return;
          setAtPath(d, containerPath, reinsertKey(container, key, target));
          commit(d);
        },

        /** Insert a clone of `schema` under the container node at `parentPath`. */
        insert(parentPath, schema, baseName) {
          const d = deepClone(state.data);
          const parent = getAtPath(d, parentPath);
          if (!parent) return null;
          const collKey = childCollectionKey(parent);
          if (!parent[collKey]) parent[collKey] = {};
          const key = genUniqueKey(parent[collKey], baseName || schema.type || 'element');
          parent[collKey][key] = deepClone(schema);
          commit(d);
          const newPath = `${parentPath}.${collKey}.${key}`;
          api.select(newPath);
          return newPath;
        },

        /** Move element at `srcPath` into the container node at `destNodePath`. */
        move(srcPath, destNodePath) {
          if (!srcPath || !destNodePath || destNodePath === srcPath) return;
          if (destNodePath.startsWith(srcPath + '.')) return; // no moving into own subtree
          const d = deepClone(state.data);
          const src = getAtPath(d, srcPath);
          const dest = getAtPath(d, destNodePath);
          if (src == null || dest == null) return;
          const { key } = containerOf(d, srcPath);
          const collKey = childCollectionKey(dest);
          if (!dest[collKey]) dest[collKey] = {};
          const newKey = genUniqueKey(dest[collKey], key);
          dest[collKey][newKey] = deepClone(src);
          deleteAtPath(d, srcPath);
          commit(d);
          api.select(`${destNodePath}.${collKey}.${newKey}`);
        },

        /** Move `srcPath` into container node `destContainerPath`, positioned just
         *  before sibling `beforeKey` (or appended when beforeKey is null/missing).
         *  Handles both same-container reorder and cross-container moves; preserves
         *  the element's key when free. Used by canvas drag-to-reorder. */
        moveTo(srcPath, destContainerPath, beforeKey) {
          if (!srcPath || !destContainerPath) return;
          if (destContainerPath === srcPath || destContainerPath.startsWith(srcPath + '.')) return;
          const d = deepClone(state.data);
          const src = getAtPath(d, srcPath);
          const dest = getAtPath(d, destContainerPath);
          if (src == null || dest == null) return;
          const srcVal = deepClone(src);
          const { container: srcContainer, key: srcKey } = containerOf(d, srcPath);
          if (srcContainer) delete srcContainer[srcKey];
          const collKey = childCollectionKey(dest);
          if (!dest[collKey] || typeof dest[collKey] !== 'object') dest[collKey] = {};
          const coll = dest[collKey];
          const newKey = (coll[srcKey] === undefined) ? srcKey : genUniqueKey(coll, srcKey);
          const out = {};
          let placed = false;
          for (const [k, v] of Object.entries(coll)) {
            if (k === beforeKey && !placed) { out[newKey] = srcVal; placed = true; }
            out[k] = v;
          }
          if (!placed) out[newKey] = srcVal;
          dest[collKey] = out;
          commit(d);
          api.select(`${destContainerPath}.${collKey}.${newKey}`);
        },

        markSaved() { state = { ...state, dirty: false }; notify(); },
        setFilePath(p) { state = { ...state, filePath: p }; notify(); },
      };
      return api;
    },
  };

  /** React hook: re-render on store change, return current state snapshot. */
  window.useEditorStore = (store) => {
    const [, force] = React.useReducer((x) => x + 1, 0);
    React.useEffect(() => (store ? store.subscribe(force) : undefined), [store]);
    return store ? store.getState() : null;
  };
})();
