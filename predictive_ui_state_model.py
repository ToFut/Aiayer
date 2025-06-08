#!/usr/bin/env python3
"""
Predictive UI State Model
Advanced system that predicts UI state changes and element locations based on context and history.
Enables more accurate targeting by anticipating where elements will be and how they'll respond.
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/predictive_ui_model.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("predictive_ui_model")

# Try to import ML dependencies (optional)
try:
    import tensorflow as tf
    import tensorflow_probability as tfp
    ML_AVAILABLE = True
    logger.info("✅ ML dependencies loaded")
except ImportError:
    ML_AVAILABLE = False
    logger.warning("⚠️ ML dependencies not available, using simplified models")

@dataclass
class UIState:
    """Representation of UI state at a point in time"""
    state_id: str
    timestamp: float
    elements: Dict[str, Dict[str, Any]]
    active_element_id: Optional[str] = None
    application_name: Optional[str] = None
    window_title: Optional[str] = None
    
    def get_element_by_id(self, element_id: str) -> Optional[Dict[str, Any]]:
        """Get element by ID"""
        return self.elements.get(element_id)
    
    def get_element_by_name(self, name: str, partial: bool = True) -> Optional[Dict[str, Any]]:
        """Find element by name/text"""
        for element_id, element in self.elements.items():
            element_name = element.get("name", "") or element.get("text", "")
            if element_name:
                if partial and name.lower() in element_name.lower():
                    return element
                elif not partial and name.lower() == element_name.lower():
                    return element
        return None

@dataclass
class UITransition:
    """Representation of a transition between two UI states"""
    transition_id: str
    from_state_id: str
    to_state_id: str
    action: Dict[str, Any]  # action that caused the transition
    timestamp: float
    duration: float  # time taken for transition
    element_changes: Dict[str, Dict[str, Any]]  # changed elements

@dataclass
class StatePrediction:
    """Prediction about future UI state"""
    from_state_id: str
    predicted_elements: Dict[str, Dict[str, Any]]
    confidence: float
    predicted_at: float
    action: Dict[str, Any]
    predicted_duration: float
    
    def compare_with_actual(self, actual_state: UIState) -> Dict[str, Any]:
        """Compare prediction with actual state"""
        comparison = {
            "timestamp": time.time(),
            "prediction_id": f"{self.from_state_id}_{int(self.predicted_at)}",
            "actual_state_id": actual_state.state_id,
            "accuracy": 0.0,
            "element_accuracy": {},
            "timing_accuracy": 0.0,
            "summary": ""
        }
        
        # Compare elements
        matched_elements = 0
        total_predicted = len(self.predicted_elements)
        total_actual = len(actual_state.elements)
        
        for element_id, predicted in self.predicted_elements.items():
            # Try to find matching element in actual state
            actual = None
            
            # Direct ID match (best case)
            if element_id in actual_state.elements:
                actual = actual_state.elements[element_id]
                comparison["element_accuracy"][element_id] = 1.0
                matched_elements += 1
                continue
            
            # Try to match by properties
            if "name" in predicted and predicted["name"]:
                actual = actual_state.get_element_by_name(predicted["name"])
                
                if actual:
                    # Calculate position accuracy if bounds available
                    if "bounds" in predicted and "bounds" in actual:
                        p_x1, p_y1, p_x2, p_y2 = predicted["bounds"]
                        a_x1, a_y1, a_x2, a_y2 = actual["bounds"]
                        
                        # Calculate center points
                        p_cx = (p_x1 + p_x2) / 2
                        p_cy = (p_y1 + p_y2) / 2
                        a_cx = (a_x1 + a_x2) / 2
                        a_cy = (a_y1 + a_y2) / 2
                        
                        # Calculate distance between centers
                        distance = ((p_cx - a_cx) ** 2 + (p_cy - a_cy) ** 2) ** 0.5
                        
                        # Normalize by screen size (assuming 1920x1080 for example)
                        screen_diagonal = (1920 ** 2 + 1080 ** 2) ** 0.5
                        normalized_distance = distance / screen_diagonal
                        
                        # Convert to accuracy (1.0 = perfect, 0.0 = far off)
                        position_accuracy = max(0.0, 1.0 - normalized_distance)
                        comparison["element_accuracy"][element_id] = position_accuracy
                        
                        if position_accuracy > 0.7:  # Consider as matched if accuracy is high
                            matched_elements += 1
                    else:
                        # Without bounds, just consider it a match
                        comparison["element_accuracy"][element_id] = 0.5
                        matched_elements += 0.5
        
        # Calculate overall element accuracy
        if total_predicted > 0:
            comparison["accuracy"] = matched_elements / total_predicted
        
        # Generate summary
        comparison["summary"] = f"Predicted {total_predicted} elements, found {matched_elements} matches in actual state with {total_actual} elements."
        
        return comparison

class ElementTracker:
    """Tracks UI elements across states to build transition models"""
    
    def __init__(self):
        self.element_history = defaultdict(list)  # element_id -> list of states
        self.position_history = defaultdict(list)  # element_id -> list of positions (for trajectory modeling)
        
        # Element similarity threshold
        self.similarity_threshold = 0.8
    
    def update(self, state: UIState):
        """Update element tracking with a new state"""
        for element_id, element in state.elements.items():
            # If we've seen this exact element ID before, update its history
            if element_id in self.element_history:
                self.element_history[element_id].append({
                    "state_id": state.state_id,
                    "timestamp": state.timestamp,
                    "element": element
                })
                
                # Update position history if bounds are available
                if "bounds" in element:
                    x1, y1, x2, y2 = element["bounds"]
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    self.position_history[element_id].append({
                        "timestamp": state.timestamp,
                        "position": (cx, cy)
                    })
            else:
                # Check if this is a new instance of an element we've seen before
                matched_id = self._find_matching_element(element)
                
                if matched_id:
                    # Found a match - use existing ID for continuity
                    self.element_history[matched_id].append({
                        "state_id": state.state_id,
                        "timestamp": state.timestamp,
                        "element": element
                    })
                    
                    # Update position history
                    if "bounds" in element:
                        x1, y1, x2, y2 = element["bounds"]
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        self.position_history[matched_id].append({
                            "timestamp": state.timestamp,
                            "position": (cx, cy)
                        })
                else:
                    # Truly new element - start tracking it
                    self.element_history[element_id].append({
                        "state_id": state.state_id,
                        "timestamp": state.timestamp,
                        "element": element
                    })
                    
                    # Initialize position history
                    if "bounds" in element:
                        x1, y1, x2, y2 = element["bounds"]
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        self.position_history[element_id].append({
                            "timestamp": state.timestamp,
                            "position": (cx, cy)
                        })
    
    def _find_matching_element(self, element: Dict[str, Any]) -> Optional[str]:
        """Find if this element matches one we've seen before"""
        best_match_id = None
        best_match_score = 0.0
        
        # Get element properties for matching
        element_name = element.get("name", "") or element.get("text", "")
        element_type = element.get("type", "")
        element_bounds = element.get("bounds")
        
        for tracked_id, history in self.element_history.items():
            if not history:
                continue
                
            # Get most recent state of this tracked element
            last_state = history[-1]
            tracked = last_state["element"]
            
            # Skip if basic properties don't match
            tracked_name = tracked.get("name", "") or tracked.get("text", "")
            tracked_type = tracked.get("type", "")
            
            if element_type != tracked_type:
                continue
            
            # Calculate similarity score
            similarity = 0.0
            
            # Name similarity (weighted highly)
            if element_name and tracked_name:
                if element_name.lower() == tracked_name.lower():
                    similarity += 0.6
                elif element_name.lower() in tracked_name.lower() or tracked_name.lower() in element_name.lower():
                    similarity += 0.3
            
            # Position similarity (if bounds available)
            if element_bounds and "bounds" in tracked:
                e_x1, e_y1, e_x2, e_y2 = element_bounds
                t_x1, t_y1, t_x2, t_y2 = tracked["bounds"]
                
                # Calculate center points
                e_cx = (e_x1 + e_x2) / 2
                e_cy = (e_y1 + e_y2) / 2
                t_cx = (t_x1 + t_x2) / 2
                t_cy = (t_y1 + t_y2) / 2
                
                # Calculate distance between centers
                distance = ((e_cx - t_cx) ** 2 + (e_cy - t_cy) ** 2) ** 0.5
                
                # Normalize by screen size (assuming 1920x1080 for example)
                screen_diagonal = (1920 ** 2 + 1080 ** 2) ** 0.5
                normalized_distance = distance / screen_diagonal
                
                # Convert to similarity (1.0 = identical, 0.0 = far apart)
                position_similarity = max(0.0, 1.0 - normalized_distance)
                similarity += 0.4 * position_similarity
            
            # Update best match if better
            if similarity > best_match_score and similarity >= self.similarity_threshold:
                best_match_score = similarity
                best_match_id = tracked_id
        
        return best_match_id
    
    def predict_element_position(self, element_id: str, future_time: float) -> Optional[Tuple[float, float]]:
        """Predict future position of an element based on its trajectory"""
        if element_id not in self.position_history or len(self.position_history[element_id]) < 2:
            return None
        
        # Get position history for this element
        history = self.position_history[element_id]
        
        # If history is too short, return the last known position
        if len(history) < 2:
            return history[-1]["position"]
        
        # If we have enough history, use linear regression to predict future position
        timestamps = np.array([entry["timestamp"] for entry in history])
        positions_x = np.array([entry["position"][0] for entry in history])
        positions_y = np.array([entry["position"][1] for entry in history])
        
        # Normalize timestamps
        t_min = timestamps.min()
        timestamps = timestamps - t_min
        future_time_normalized = future_time - t_min
        
        # Check if element is moving
        if np.std(positions_x) < 1.0 and np.std(positions_y) < 1.0:
            # Element is stationary, return last position
            return history[-1]["position"]
        
        # Simple linear regression
        try:
            # For X coordinate
            A = np.vstack([timestamps, np.ones(len(timestamps))]).T
            m_x, c_x = np.linalg.lstsq(A, positions_x, rcond=None)[0]
            
            # For Y coordinate
            m_y, c_y = np.linalg.lstsq(A, positions_y, rcond=None)[0]
            
            # Predict future position
            future_x = m_x * future_time_normalized + c_x
            future_y = m_y * future_time_normalized + c_y
            
            return (future_x, future_y)
        except:
            # Fallback to last known position
            return history[-1]["position"]

class TransitionModel:
    """Models UI state transitions to predict future states"""
    
    def __init__(self):
        self.transitions = []  # List of UITransition objects
        self.state_cache = {}  # state_id -> UIState
        self.element_tracker = ElementTracker()
        
        # If ML is available, we can use more sophisticated models
        self.ml_enabled = ML_AVAILABLE
        self.transition_model = None
        
        if self.ml_enabled:
            self._init_ml_model()
    
    def _init_ml_model(self):
        """Initialize ML model for transition prediction"""
        # This would be a more sophisticated model in production
        # For now, we use a simple placeholder
        logger.info("Initializing ML transition model")
    
    def add_state(self, state: UIState):
        """Add a new UI state to the model"""
        # Cache the state
        self.state_cache[state.state_id] = state
        
        # Update element tracking
        self.element_tracker.update(state)
        
        # If we have previous states, create transition
        state_ids = list(self.state_cache.keys())
        if len(state_ids) > 1:
            # Find the most recent previous state
            prev_states = [(s_id, self.state_cache[s_id]) for s_id in state_ids if s_id != state.state_id]
            prev_states.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            if prev_states:
                prev_state_id, prev_state = prev_states[0]
                
                # Only create transition if this state is newer
                if state.timestamp > prev_state.timestamp:
                    # Create a transition
                    transition = UITransition(
                        transition_id=f"{prev_state_id}_to_{state.state_id}",
                        from_state_id=prev_state_id,
                        to_state_id=state.state_id,
                        action={"type": "unknown"},  # Placeholder, would be filled with actual action
                        timestamp=state.timestamp,
                        duration=state.timestamp - prev_state.timestamp,
                        element_changes=self._compute_element_changes(prev_state, state)
                    )
                    
                    self.transitions.append(transition)
                    logger.debug(f"Added transition: {transition.transition_id}")
    
    def add_transition(self, from_state: UIState, to_state: UIState, action: Dict[str, Any]):
        """Add a transition between two states with the action that caused it"""
        # Cache states
        self.state_cache[from_state.state_id] = from_state
        self.state_cache[to_state.state_id] = to_state
        
        # Update element tracking for both states
        self.element_tracker.update(from_state)
        self.element_tracker.update(to_state)
        
        # Create transition
        transition = UITransition(
            transition_id=f"{from_state.state_id}_to_{to_state.state_id}",
            from_state_id=from_state.state_id,
            to_state_id=to_state.state_id,
            action=action,
            timestamp=to_state.timestamp,
            duration=to_state.timestamp - from_state.timestamp,
            element_changes=self._compute_element_changes(from_state, to_state)
        )
        
        self.transitions.append(transition)
        logger.debug(f"Added transition with action: {action.get('type', 'unknown')}")
    
    def _compute_element_changes(self, from_state: UIState, to_state: UIState) -> Dict[str, Dict[str, Any]]:
        """Compute changes between two states"""
        changes = {}
        
        # Set of element IDs in both states
        from_ids = set(from_state.elements.keys())
        to_ids = set(to_state.elements.keys())
        
        # Elements in both states - check for changes
        for element_id in from_ids.intersection(to_ids):
            from_element = from_state.elements[element_id]
            to_element = to_state.elements[element_id]
            
            # Compute differences
            diff = {}
            
            for key in set(from_element.keys()).union(set(to_element.keys())):
                # Skip internal tracking fields
                if key.startswith("_"):
                    continue
                
                if key not in from_element:
                    diff[key] = {"from": None, "to": to_element[key]}
                elif key not in to_element:
                    diff[key] = {"from": from_element[key], "to": None}
                elif from_element[key] != to_element[key]:
                    diff[key] = {"from": from_element[key], "to": to_element[key]}
            
            # If we found differences, add to changes
            if diff:
                changes[element_id] = {
                    "type": "modified",
                    "changes": diff
                }
        
        # Elements only in from_state - removed
        for element_id in from_ids - to_ids:
            changes[element_id] = {
                "type": "removed",
                "element": from_state.elements[element_id]
            }
        
        # Elements only in to_state - added
        for element_id in to_ids - from_ids:
            changes[element_id] = {
                "type": "added",
                "element": to_state.elements[element_id]
            }
        
        return changes
    
    def predict_next_state(self, current_state: UIState, action: Dict[str, Any]) -> StatePrediction:
        """Predict the next state based on current state and action"""
        # Find similar states and transitions
        similar_states = self._find_similar_states(current_state)
        
        if not similar_states:
            # No similar states found, use fallback prediction
            return self._predict_fallback(current_state, action)
        
        # Find transitions from similar states with similar actions
        relevant_transitions = []
        
        for state_id, similarity in similar_states:
            # Find transitions from this state
            for transition in self.transitions:
                if transition.from_state_id == state_id:
                    # Check if action is similar
                    action_similarity = self._compare_actions(transition.action, action)
                    
                    if action_similarity > 0.7:  # Threshold for action similarity
                        # Combine state and action similarity
                        combined_similarity = (similarity + action_similarity) / 2
                        
                        relevant_transitions.append((transition, combined_similarity))
        
        if not relevant_transitions:
            # No relevant transitions found, use fallback
            return self._predict_fallback(current_state, action)
        
        # Sort transitions by similarity (highest first)
        relevant_transitions.sort(key=lambda x: x[1], reverse=True)
        
        # Use the most similar transition as a base for prediction
        best_transition, best_similarity = relevant_transitions[0]
        
        # Get the resulting state
        if best_transition.to_state_id in self.state_cache:
            result_state = self.state_cache[best_transition.to_state_id]
            
            # Create prediction based on the resulting state, adjusted for current context
            predicted_elements = {}
            
            for element_id, element in result_state.elements.items():
                # Copy the element
                predicted_element = element.copy()
                
                # If this element exists in current state, adjust position based on trajectory
                if element_id in current_state.elements:
                    # Get current bounds
                    current_element = current_state.elements[element_id]
                    
                    if "bounds" in current_element and "bounds" in predicted_element:
                        # Use current position as base
                        predicted_element["bounds"] = current_element["bounds"]
                
                # Predict future position based on element tracking
                future_time = current_state.timestamp + best_transition.duration
                predicted_position = self.element_tracker.predict_element_position(element_id, future_time)
                
                if predicted_position and "bounds" in predicted_element:
                    # Update bounds based on predicted center
                    x1, y1, x2, y2 = predicted_element["bounds"]
                    width = x2 - x1
                    height = y2 - y1
                    
                    px, py = predicted_position
                    new_x1 = px - width / 2
                    new_y1 = py - height / 2
                    new_x2 = px + width / 2
                    new_y2 = py + height / 2
                    
                    predicted_element["bounds"] = (new_x1, new_y1, new_x2, new_y2)
                
                predicted_elements[element_id] = predicted_element
            
            # Create prediction
            prediction = StatePrediction(
                from_state_id=current_state.state_id,
                predicted_elements=predicted_elements,
                confidence=best_similarity,
                predicted_at=time.time(),
                action=action,
                predicted_duration=best_transition.duration
            )
            
            return prediction
        else:
            # State not in cache, use fallback
            return self._predict_fallback(current_state, action)
    
    def _find_similar_states(self, state: UIState) -> List[Tuple[str, float]]:
        """Find states similar to the given state"""
        similar_states = []
        
        for state_id, cached_state in self.state_cache.items():
            # Skip comparing to itself
            if state_id == state.state_id:
                continue
            
            # Calculate similarity score
            similarity = self._compare_states(state, cached_state)
            
            if similarity > 0.6:  # Threshold for similarity
                similar_states.append((state_id, similarity))
        
        # Sort by similarity (highest first)
        similar_states.sort(key=lambda x: x[1], reverse=True)
        
        return similar_states
    
    def _compare_states(self, state1: UIState, state2: UIState) -> float:
        """Compare two states and return similarity score (0.0 to 1.0)"""
        # Compare application and window
        app_match = state1.application_name and state2.application_name and state1.application_name == state2.application_name
        title_match = state1.window_title and state2.window_title and state1.window_title == state2.window_title
        
        # Base similarity on application/window match
        if app_match and title_match:
            base_similarity = 0.7
        elif app_match:
            base_similarity = 0.5
        else:
            base_similarity = 0.2
        
        # Compare elements
        elements1 = state1.elements
        elements2 = state2.elements
        
        # If element counts are vastly different, reduce similarity
        count_ratio = min(len(elements1), len(elements2)) / max(len(elements1), len(elements2)) if elements1 and elements2 else 0
        element_count_similarity = count_ratio * 0.2
        
        # Compare individual elements
        element_similarities = []
        
        for element_id, element1 in elements1.items():
            # Try to find matching element in state2
            best_match_score = 0.0
            
            for element2 in elements2.values():
                # Compare element properties
                match_score = self._compare_elements(element1, element2)
                best_match_score = max(best_match_score, match_score)
            
            element_similarities.append(best_match_score)
        
        # Calculate average element similarity
        avg_element_similarity = sum(element_similarities) / len(element_similarities) if element_similarities else 0
        
        # Combine scores
        final_similarity = base_similarity * 0.3 + element_count_similarity + avg_element_similarity * 0.5
        
        return min(1.0, final_similarity)  # Cap at 1.0
    
    def _compare_elements(self, element1: Dict[str, Any], element2: Dict[str, Any]) -> float:
        """Compare two elements and return similarity score (0.0 to 1.0)"""
        # Compare basic properties
        type_match = element1.get("type") == element2.get("type")
        
        # Name/text matching
        name1 = element1.get("name", "") or element1.get("text", "")
        name2 = element2.get("name", "") or element2.get("text", "")
        
        name_similarity = 0.0
        if name1 and name2:
            if name1.lower() == name2.lower():
                name_similarity = 1.0
            elif name1.lower() in name2.lower() or name2.lower() in name1.lower():
                name_similarity = 0.7
        
        # Position similarity
        position_similarity = 0.0
        if "bounds" in element1 and "bounds" in element2:
            # Get bounds
            x1_1, y1_1, x2_1, y2_1 = element1["bounds"]
            x1_2, y1_2, x2_2, y2_2 = element2["bounds"]
            
            # Calculate center points
            cx1 = (x1_1 + x2_1) / 2
            cy1 = (y1_1 + y2_1) / 2
            cx2 = (x1_2 + x2_2) / 2
            cy2 = (y1_2 + y2_2) / 2
            
            # Calculate distance between centers
            distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
            
            # Normalize by screen size (assuming 1920x1080 for example)
            screen_diagonal = (1920 ** 2 + 1080 ** 2) ** 0.5
            normalized_distance = distance / screen_diagonal
            
            # Convert to similarity
            position_similarity = max(0.0, 1.0 - normalized_distance)
        
        # Combine scores with appropriate weights
        if type_match:
            return 0.3 + name_similarity * 0.4 + position_similarity * 0.3
        else:
            return name_similarity * 0.4 + position_similarity * 0.3
    
    def _compare_actions(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> float:
        """Compare two actions and return similarity score (0.0 to 1.0)"""
        # Compare action types
        type_match = action1.get("type") == action2.get("type")
        
        if not type_match:
            return 0.0
        
        # For different action types, compute similarity differently
        action_type = action1.get("type")
        
        if action_type == "click":
            # Compare click targets
            target1 = action1.get("target", {})
            target2 = action2.get("target", {})
            
            # If targets are element IDs
            if isinstance(target1, str) and isinstance(target2, str):
                return 1.0 if target1 == target2 else 0.0
            
            # If targets are elements with properties
            if isinstance(target1, dict) and isinstance(target2, dict):
                # Compare element properties
                properties_similarity = []
                
                # Compare types
                if "type" in target1 and "type" in target2:
                    properties_similarity.append(1.0 if target1["type"] == target2["type"] else 0.0)
                
                # Compare names
                name1 = target1.get("name", "") or target1.get("text", "")
                name2 = target2.get("name", "") or target2.get("text", "")
                
                if name1 and name2:
                    if name1.lower() == name2.lower():
                        properties_similarity.append(1.0)
                    elif name1.lower() in name2.lower() or name2.lower() in name1.lower():
                        properties_similarity.append(0.7)
                    else:
                        properties_similarity.append(0.0)
                
                # Compare positions
                if "center" in target1 and "center" in target2:
                    x1, y1 = target1["center"]
                    x2, y2 = target2["center"]
                    
                    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
                    screen_diagonal = (1920 ** 2 + 1080 ** 2) ** 0.5
                    normalized_distance = distance / screen_diagonal
                    
                    position_similarity = max(0.0, 1.0 - normalized_distance)
                    properties_similarity.append(position_similarity)
                
                # Calculate average similarity
                return sum(properties_similarity) / len(properties_similarity) if properties_similarity else 0.0
            
            return 0.5  # Default if targets can't be compared
            
        elif action_type == "type":
            # Compare text values
            text1 = action1.get("text", "")
            text2 = action2.get("text", "")
            
            if text1 and text2:
                if text1 == text2:
                    return 1.0
                elif text1 in text2 or text2 in text1:
                    return 0.7
                else:
                    return 0.3
            
            return 0.5  # Default if text can't be compared
            
        elif action_type == "key":
            # Compare key values
            key1 = action1.get("key", "")
            key2 = action2.get("key", "")
            
            return 1.0 if key1 == key2 else 0.0
            
        else:
            # Default comparison
            return 0.5 if type_match else 0.0
    
    def _predict_fallback(self, current_state: UIState, action: Dict[str, Any]) -> StatePrediction:
        """Fallback prediction when no similar states/transitions are found"""
        # Create a copy of current elements as the base prediction
        predicted_elements = {}
        
        for element_id, element in current_state.elements.items():
            predicted_elements[element_id] = element.copy()
        
        # Predict duration based on action type
        if action.get("type") == "click":
            predicted_duration = 0.5  # Half second for click responses
        elif action.get("type") == "type":
            # Duration based on text length
            text_length = len(action.get("text", ""))
            predicted_duration = 0.2 + text_length * 0.05  # Base + per character
        elif action.get("type") == "key":
            predicted_duration = 0.3  # Key press response
        else:
            predicted_duration = 1.0  # Default fallback
        
        # Create prediction with low confidence
        prediction = StatePrediction(
            from_state_id=current_state.state_id,
            predicted_elements=predicted_elements,
            confidence=0.3,  # Low confidence for fallback
            predicted_at=time.time(),
            action=action,
            predicted_duration=predicted_duration
        )
        
        return prediction

class PredictiveUIStateModel:
    """Main class for predictive UI state modeling"""
    
    def __init__(self):
        self.transition_model = TransitionModel()
        self.current_state = None
        self.history = []  # List of past states
        self.max_history = 20
        
        # Predictions tracking
        self.predictions = []
        self.max_predictions = 10
        
        # Learning parameters
        self.learning_enabled = True
        self.min_confidence_threshold = 0.4  # Minimum confidence to trust predictions
        
        logger.info("✅ Predictive UI State Model initialized")
    
    def update_state(self, elements: Dict[str, Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Update the model with a new UI state"""
        if not metadata:
            metadata = {}
        
        # Create a new state
        state_id = f"state_{int(time.time() * 1000)}"
        state = UIState(
            state_id=state_id,
            timestamp=time.time(),
            elements=elements,
            application_name=metadata.get("application_name"),
            window_title=metadata.get("window_title"),
            active_element_id=metadata.get("active_element_id")
        )
        
        # If we have a current state, this is a transition
        if self.current_state:
            # Add state to the transition model
            self.transition_model.add_state(state)
            
            # Evaluate predictions if we have any
            self._evaluate_predictions(state)
        
        # Update current state
        self.current_state = state
        
        # Add to history
        self.history.append(state)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        logger.debug(f"State updated: {state_id} with {len(elements)} elements")
    
    def record_action(self, action: Dict[str, Any], result_elements: Dict[str, Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Record an action and its resulting state"""
        if not self.current_state:
            logger.warning("Cannot record action: no current state")
            return
        
        if not metadata:
            metadata = {}
        
        # Create a new state for the result
        state_id = f"state_{int(time.time() * 1000)}"
        result_state = UIState(
            state_id=state_id,
            timestamp=time.time(),
            elements=result_elements,
            application_name=metadata.get("application_name"),
            window_title=metadata.get("window_title"),
            active_element_id=metadata.get("active_element_id")
        )
        
        # Add transition with the action
        self.transition_model.add_transition(self.current_state, result_state, action)
        
        # Evaluate predictions if we have any
        self._evaluate_predictions(result_state)
        
        # Update current state
        self.current_state = result_state
        
        # Add to history
        self.history.append(result_state)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        logger.debug(f"Action recorded: {action.get('type', 'unknown')}, new state: {state_id}")
    
    def predict_next_state(self, action: Dict[str, Any]) -> Optional[StatePrediction]:
        """Predict the next state based on the current state and action"""
        if not self.current_state:
            logger.warning("Cannot predict next state: no current state")
            return None
        
        # Get prediction from transition model
        prediction = self.transition_model.predict_next_state(self.current_state, action)
        
        # Add to predictions
        self.predictions.append(prediction)
        
        # Limit predictions size
        if len(self.predictions) > self.max_predictions:
            self.predictions = self.predictions[-self.max_predictions:]
        
        logger.debug(f"Predicted next state with confidence: {prediction.confidence:.2f}")
        
        return prediction
    
    def predict_element_position(self, element_id: str, future_time_delta: float = 0.5) -> Optional[Tuple[float, float]]:
        """Predict the future position of an element"""
        if not self.current_state or element_id not in self.current_state.elements:
            logger.warning(f"Cannot predict position: element {element_id} not in current state")
            return None
        
        # Calculate future time
        future_time = time.time() + future_time_delta
        
        # Use element tracker to predict position
        return self.transition_model.element_tracker.predict_element_position(element_id, future_time)
    
    def get_target_for_action(self, action_type: str, target_description: Dict[str, Any]) -> Dict[str, Any]:
        """Find the best UI element to target for a given action"""
        if not self.current_state:
            logger.warning("Cannot get target: no current state")
            return {"success": False, "error": "No current state"}
        
        # Different handling based on action type
        if action_type == "click":
            return self._find_click_target(target_description)
        elif action_type == "type":
            return self._find_text_input_target(target_description)
        else:
            return {"success": False, "error": f"Unsupported action type: {action_type}"}
    
    def _find_click_target(self, target_description: Dict[str, Any]) -> Dict[str, Any]:
        """Find the best element to click based on description"""
        elements = self.current_state.elements
        
        # If exact element ID is provided
        if "element_id" in target_description and target_description["element_id"] in elements:
            element = elements[target_description["element_id"]]
            return {
                "success": True,
                "element_id": target_description["element_id"],
                "element": element,
                "confidence": 1.0
            }
        
        # Search by text/name
        if "text" in target_description:
            text = target_description["text"]
            element = self.current_state.get_element_by_name(text, partial=True)
            
            if element:
                return {
                    "success": True,
                    "element_id": next(e_id for e_id, e in elements.items() if e is element),
                    "element": element,
                    "confidence": 0.9 if text.lower() == (element.get("name", "") or element.get("text", "")).lower() else 0.7
                }
        
        # Search by type and position
        if "type" in target_description:
            element_type = target_description["type"]
            matching_elements = [
                (e_id, e) for e_id, e in elements.items() 
                if e.get("type") == element_type
            ]
            
            if matching_elements:
                # If position is provided, find closest
                if "position" in target_description:
                    target_x, target_y = target_description["position"]
                    
                    closest_element = None
                    closest_distance = float('inf')
                    
                    for e_id, element in matching_elements:
                        if "bounds" in element:
                            x1, y1, x2, y2 = element["bounds"]
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            
                            distance = ((center_x - target_x) ** 2 + (center_y - target_y) ** 2) ** 0.5
                            
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_element = (e_id, element)
                    
                    if closest_element:
                        e_id, element = closest_element
                        
                        # Calculate confidence based on distance
                        screen_diagonal = (1920 ** 2 + 1080 ** 2) ** 0.5
                        normalized_distance = closest_distance / screen_diagonal
                        confidence = max(0.3, 1.0 - normalized_distance)
                        
                        return {
                            "success": True,
                            "element_id": e_id,
                            "element": element,
                            "confidence": confidence
                        }
                
                # If no position or no match with position, return first matching element
                e_id, element = matching_elements[0]
                return {
                    "success": True,
                    "element_id": e_id,
                    "element": element,
                    "confidence": 0.5
                }
        
        # If no matches, return failure
        return {
            "success": False,
            "error": "No matching element found",
            "available_elements": [
                {"id": e_id, "type": e.get("type"), "name": e.get("name") or e.get("text")}
                for e_id, e in list(elements.items())[:5]  # First 5 elements as samples
            ]
        }
    
    def _find_text_input_target(self, target_description: Dict[str, Any]) -> Dict[str, Any]:
        """Find the best text input element based on description"""
        elements = self.current_state.elements
        
        # If exact element ID is provided
        if "element_id" in target_description and target_description["element_id"] in elements:
            element = elements[target_description["element_id"]]
            return {
                "success": True,
                "element_id": target_description["element_id"],
                "element": element,
                "confidence": 1.0
            }
        
        # Find editable elements
        editable_elements = [
            (e_id, e) for e_id, e in elements.items()
            if e.get("type") in ["textfield", "textarea", "input", "editbox", "text"]
        ]
        
        if not editable_elements:
            return {
                "success": False,
                "error": "No text input elements found",
                "available_elements": [
                    {"id": e_id, "type": e.get("type"), "name": e.get("name") or e.get("text")}
                    for e_id, e in list(elements.items())[:5]  # First 5 elements as samples
                ]
            }
        
        # Search by name/label
        if "label" in target_description:
            label = target_description["label"]
            
            for e_id, element in editable_elements:
                element_name = element.get("name", "") or element.get("text", "")
                
                if element_name and label.lower() in element_name.lower():
                    return {
                        "success": True,
                        "element_id": e_id,
                        "element": element,
                        "confidence": 0.9 if label.lower() == element_name.lower() else 0.7
                    }
        
        # If no specific match, return the first editable element
        e_id, element = editable_elements[0]
        return {
            "success": True,
            "element_id": e_id,
            "element": element,
            "confidence": 0.5
        }
    
    def _evaluate_predictions(self, actual_state: UIState):
        """Evaluate the accuracy of predictions against actual state"""
        if not self.predictions:
            return
        
        # Filter predictions to those that haven't been evaluated yet
        pending_predictions = [p for p in self.predictions if not hasattr(p, "evaluation")]
        
        for prediction in pending_predictions:
            # Compare prediction with actual state
            evaluation = prediction.compare_with_actual(actual_state)
            
            # Add evaluation to prediction
            setattr(prediction, "evaluation", evaluation)
            
            # Log evaluation
            logger.debug(f"Prediction evaluation: accuracy {evaluation['accuracy']:.2f}, summary: {evaluation['summary']}")
            
            # Use evaluation for learning (if enabled)
            if self.learning_enabled:
                self._learn_from_evaluation(prediction, evaluation)
    
    def _learn_from_evaluation(self, prediction: StatePrediction, evaluation: Dict[str, Any]):
        """Learn from prediction evaluation to improve future predictions"""
        # Placeholder for learning implementation
        # In a full implementation, this would update weights, thresholds, etc.
        pass

# Create singleton instance
predictive_ui_model = PredictiveUIStateModel()

async def main():
    """Test the predictive UI state model"""
    # Create some test states and actions
    state1_elements = {
        "button1": {
            "type": "button",
            "name": "Submit",
            "bounds": (100, 200, 200, 230),
        },
        "input1": {
            "type": "textfield",
            "name": "Username",
            "bounds": (100, 150, 300, 180),
            "value": ""
        }
    }
    
    # Update the model with initial state
    print("Adding initial state...")
    predictive_ui_model.update_state(state1_elements, {"application_name": "TestApp", "window_title": "Login"})
    
    # Define a click action
    click_action = {
        "type": "click",
        "target": {"type": "button", "text": "Submit"}
    }
    
    # Predict next state after click
    print("\nPredicting next state after click...")
    prediction = predictive_ui_model.predict_next_state(click_action)
    
    print(f"Prediction confidence: {prediction.confidence:.2f}")
    print(f"Predicted elements: {len(prediction.predicted_elements)}")
    
    # Create a result state (simulating what would happen after the click)
    state2_elements = {
        "message": {
            "type": "text",
            "name": "Please enter your password",
            "bounds": (100, 100, 350, 130),
        },
        "input2": {
            "type": "textfield",
            "name": "Password",
            "bounds": (100, 150, 300, 180),
            "value": ""
        }
    }
    
    # Record the action and its result
    print("\nRecording action and result...")
    predictive_ui_model.record_action(click_action, state2_elements, {"application_name": "TestApp", "window_title": "Login"})
    
    # Try finding a target for a new action
    print("\nFinding target for text input...")
    target_result = predictive_ui_model.get_target_for_action("type", {"label": "Password"})
    
    if target_result["success"]:
        print(f"Found target: {target_result['element'].get('name')} with confidence {target_result['confidence']:.2f}")
    else:
        print(f"Target not found: {target_result['error']}")
    
    # Define a type action
    type_action = {
        "type": "type",
        "target": target_result.get("element_id"),
        "text": "mypassword"
    }
    
    # Predict next state after typing
    print("\nPredicting next state after typing...")
    prediction2 = predictive_ui_model.predict_next_state(type_action)
    
    print(f"Prediction confidence: {prediction2.confidence:.2f}")
    print(f"Predicted elements: {len(prediction2.predicted_elements)}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())