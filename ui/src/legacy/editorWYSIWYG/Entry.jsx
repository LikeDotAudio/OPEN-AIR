/**
 * Header: Entry.jsx
 * Purpose: Entry component or utility.
 * Description: Handles logic and rendering for Entry component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Entry.jsx — launch surface for the HTML5 WYSIWYG editor.
 * Mirrors oaGuiEditorWYSIWYG/Entry.py (launch_editor).
 *
 * The editor renders as a React overlay inside the app tree (so it shares the
 * MqttProvider context and the live renderer). WindowManager owns the open state
 * and renders <window.WysiwygEditor>. For decoupled callers, launchWysiwygEditor
 * dispatches a window CustomEvent that WindowManager listens for.
 *
 *   window.launchWysiwygEditor({ filePath, content })
 */
(function () {
  window.OaEdEntry = { version: '20260522.1' };

  window.launchWysiwygEditor = (detail) => {
    window.dispatchEvent(new CustomEvent('oa-open-wysiwyg', { detail: detail || {} }));
  };
})();
