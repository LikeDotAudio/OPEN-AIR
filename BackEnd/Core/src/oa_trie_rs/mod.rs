/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaStateCache/Core/oaTrie_rs/mod.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260413.1400.1
//
// Description: Native Trie (Prefix Tree) implementation. Used 
// for rapid MQTT topic matching and address-space traversal.

use pyo3::prelude::*;
use std::collections::HashMap;

#[derive(Default)]
struct TrieNode {
    children: HashMap<String, TrieNode>,
    is_terminal: bool,
}

#[pyclass]
struct TopicTrie {
    root: TrieNode,
}

#[pymethods]
impl TopicTrie {
    #[new]
    fn new() -> Self {
        TopicTrie {
            root: TrieNode::default(),
        }
    }

    fn insert(&mut self, topic: String) {
        let mut current = &mut self.root;
        for part in topic.split('/') {
            if part.is_empty() { continue; }
            current = current.children.entry(part.to_string()).or_insert_with(TrieNode::default);
        }
        current.is_terminal = true;
    }

    fn exists(&self, prefix: String) -> bool {
        let mut current = &self.root;
        for part in prefix.split('/') {
            if part.is_empty() { continue; }
            if let Some(next) = current.children.get(part) {
                current = next;
            } else {
                return false;
            }
        }
        // If we found the node, the prefix exists in the tree
        true
    }

    fn clear(&mut self) {
        self.root = TrieNode::default();
    }
}

#[pymodule]
// Inline comment: Logic for oatrie_rs
pub fn oatrie_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TopicTrie>()?;
    Ok(())
}
