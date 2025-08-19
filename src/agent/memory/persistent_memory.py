import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import sqlite3
import json
import os
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import threading

class PersistentMemory:
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._connection = None  # Keep a single connection for in-memory databases
        
        self._initialize_db()
        
        # Only run cleanup if the database file already exists and is not in-memory
        if db_path != ":memory:" and os.path.exists(db_path):
            try:
                self._cleanup_old_data()
            except Exception as e:
                print(f"Warning: Could not cleanup old data: {e}")
    
    def _get_connection(self):
        """Get a database connection, reusing for in-memory databases"""
        if self.db_path == ":memory:":
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                self._initialize_db_for_connection(self._connection)
            return self._connection
        else:
            return sqlite3.connect(self.db_path)
    
    def _close_connection(self, conn):
        """Close connection if it's not the in-memory one"""
        if conn != self._connection:
            conn.close()
    
    def _initialize_db(self):
        """Initialize the database with required tables"""
        if self.db_path == ":memory:":
            # For in-memory databases, we'll initialize when getting connection
            return
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            self._initialize_db_for_connection(conn)
            conn.close()
    
    def _initialize_db_for_connection(self, conn):
        """Initialize tables for a specific connection"""
        cursor = conn.cursor()
        
        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                confidence REAL DEFAULT 0.5,
                last_updated REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Project patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_patterns (
                project_path TEXT,
                pattern_type TEXT,
                pattern_data TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                last_used REAL DEFAULT 0.0,
                PRIMARY KEY (project_path, pattern_type)
            )
        ''')
        
        # Tool effectiveness table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_effectiveness (
                tool_name TEXT,
                context_hash TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_execution_time REAL DEFAULT 0.0,
                last_used REAL DEFAULT 0.0,
                PRIMARY KEY (tool_name, context_hash)
            )
        ''')
        
        # Interaction history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_input TEXT,
                action TEXT,
                result TEXT,
                success INTEGER DEFAULT 0,
                timestamp REAL DEFAULT 0.0,
                project_path TEXT
            )
        ''')
        
        # Learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT,
                insight_data TEXT,
                confidence REAL DEFAULT 0.5,
                created_at REAL DEFAULT 0.0,
                last_applied REAL DEFAULT 0.0,
                times_applied INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
        ''')
        
        # File knowledge table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_knowledge (
                file_path TEXT PRIMARY KEY,
                file_type TEXT,
                last_modified REAL DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                importance_score REAL DEFAULT 0.0,
                content_hash TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent database bloat"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean interactions older than 30 days
            thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
            cursor.execute('''
                DELETE FROM interaction_history 
                WHERE timestamp < ?
            ''', (thirty_days_ago,))
            
            # Clean unused patterns older than 90 days
            ninety_days_ago = time.time() - (90 * 24 * 60 * 60)
            cursor.execute('''
                DELETE FROM project_patterns 
                WHERE last_used < ? AND usage_count < 5
            ''', (ninety_days_ago,))
            
            conn.commit()
            conn.close()
    
    def store_preference(self, key: str, value: Any, confidence: float = 0.5):
        """Store user preference with confidence score"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (key, value, confidence, last_updated, usage_count)
                VALUES (?, ?, ?, ?, COALESCE(
                    (SELECT usage_count FROM user_preferences WHERE key = ?), 0
                ) + 1)
            ''', (key, json.dumps(value), confidence, time.time(), key))
            
            conn.commit()
            self._close_connection(conn)
    
    def get_preference(self, key: str, default_value: Any = None) -> Tuple[Any, float]:
        """Get user preference and its confidence score"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value, confidence FROM user_preferences WHERE key = ?
            ''', (key,))
            result = cursor.fetchone()
            self._close_connection(conn)
            
            if result:
                try:
                    return json.loads(result[0]), result[1]
                except json.JSONDecodeError:
                    return default_value, 0.0
            return default_value, 0.0
    
    def record_tool_usage(self, tool_name: str, context_hash: str, 
                         success: bool, execution_time: float):
        """Record tool usage for effectiveness tracking"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get current stats
            cursor.execute('''
                SELECT success_count, failure_count, avg_execution_time 
                FROM tool_effectiveness 
                WHERE tool_name = ? AND context_hash = ?
            ''', (tool_name, context_hash))
            result = cursor.fetchone()
            
            if result:
                success_count, failure_count, avg_time = result
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Update average execution time
                total_executions = success_count + failure_count
                avg_time = (avg_time * (total_executions - 1) + execution_time) / total_executions
                
                cursor.execute('''
                    UPDATE tool_effectiveness 
                    SET success_count = ?, failure_count = ?, 
                        avg_execution_time = ?, last_used = ?
                    WHERE tool_name = ? AND context_hash = ?
                ''', (success_count, failure_count, avg_time, time.time(), 
                      tool_name, context_hash))
            else:
                cursor.execute('''
                    INSERT INTO tool_effectiveness 
                    (tool_name, context_hash, success_count, failure_count, 
                     avg_execution_time, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (tool_name, context_hash, 1 if success else 0, 
                      0 if success else 1, execution_time, time.time()))
            
            conn.commit()
            self._close_connection(conn)
    
    def get_tool_effectiveness(self, tool_name: str, context_hash: str) -> Dict[str, Any]:
        """Get effectiveness statistics for a tool in a specific context"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT success_count, failure_count, avg_execution_time 
                FROM tool_effectiveness 
                WHERE tool_name = ? AND context_hash = ?
            ''', (tool_name, context_hash))
            result = cursor.fetchone()
            self._close_connection(conn)
            
            if result:
                success_count, failure_count, avg_time = result
                total = success_count + failure_count
                return {
                    "success_rate": success_count / total if total > 0 else 0.5,
                    "usage_count": total,
                    "avg_execution_time": avg_time,
                    "confidence": min(1.0, total / 10)  # More usage = higher confidence
                }
            return {
                "success_rate": 0.5,
                "usage_count": 0,
                "avg_execution_time": 0.0,
                "confidence": 0.0
            }
    
    def record_interaction(self, session_id: str, user_input: str, action: Dict[str, Any], 
                         result: Dict[str, Any], project_path: str = None):
        """Record an interaction in persistent memory"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO interaction_history 
                (session_id, user_input, action, result, success, timestamp, project_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_input, json.dumps(action), 
                  json.dumps(result), result.get("success", False), 
                  time.time(), project_path or os.getcwd()))
            
            conn.commit()
            self._close_connection(conn)
    
    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions from persistent memory"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_input, action, result, success, timestamp
                FROM interaction_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            self._close_connection(conn)
            
            return [
                {
                    "user_input": row[0],
                    "action": json.loads(row[1]) if row[1] else {},
                    "result": json.loads(row[2]) if row[2] else {},
                    "success": row[3],
                    "timestamp": row[4]
                }
                for row in results
            ]
    
    def store_learning_insight(self, insight_type: str, insight_data: Any, 
                             confidence: float = 0.5):
        """Store a learning insight"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_insights 
                (insight_type, insight_data, confidence, created_at)
                VALUES (?, ?, ?, ?)
            ''', (insight_type, json.dumps(insight_data), confidence, time.time()))
            
            conn.commit()
            self._close_connection(conn)
    
    def get_learning_insights(self, insight_type: str = None) -> List[Dict[str, Any]]:
        """Get learning insights, optionally filtered by type"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if insight_type:
                cursor.execute('''
                    SELECT insight_type, insight_data, confidence, times_applied, success_rate
                    FROM learning_insights 
                    WHERE insight_type = ?
                    ORDER BY confidence DESC, created_at DESC
                ''', (insight_type,))
            else:
                cursor.execute('''
                    SELECT insight_type, insight_data, confidence, times_applied, success_rate
                    FROM learning_insights 
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT 50
                ''')
            
            results = cursor.fetchall()
            self._close_connection(conn)
            
            return [
                {
                    "insight_type": row[0],
                    "insight_data": json.loads(row[1]) if row[1] else {},
                    "confidence": row[2],
                    "times_applied": row[3],
                    "success_rate": row[4]
                }
                for row in results
            ]
    
    def update_file_knowledge(self, file_path: str, content: str = None, metadata: Dict[str, Any] = None):
        """Update knowledge about a file"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Calculate content hash if content provided
            content_hash = None
            if content:
                content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Get file extension
            file_type = os.path.splitext(file_path)[1].lower()
            
            cursor.execute('''
                INSERT OR REPLACE INTO file_knowledge 
                (file_path, file_type, last_modified, access_count, importance_score, content_hash, metadata)
                VALUES (?, ?, ?, COALESCE(
                    (SELECT access_count FROM file_knowledge WHERE file_path = ?), 0
                ) + 1, 
                COALESCE(
                    (SELECT importance_score FROM file_knowledge WHERE file_path = ?), 0.0
                ), ?, ?)
            ''', (file_path, file_type, time.time(), file_path, file_path, 
                  content_hash, json.dumps(metadata or {})))
            
            conn.commit()
            self._close_connection(conn)
    
    def get_important_files(self, project_path: str, limit: int = 10) -> List[str]:
        """Get most important files in a project"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path, importance_score, access_count
                FROM file_knowledge 
                WHERE file_path LIKE ?
                ORDER BY importance_score DESC, access_count DESC
                LIMIT ?
            ''', (f"{project_path}%", limit))
            
            results = cursor.fetchall()
            self._close_connection(conn)
            
            return [row[0] for row in results]
    
    def generate_context_hash(self, context: Dict[str, Any]) -> str:
        """Generate a hash of the context for pattern matching"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Count tables
            tables = ["user_preferences", "project_patterns", "tool_effectiveness", 
                     "interaction_history", "learning_insights", "file_knowledge"]
            
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    stats[f"{table}_count"] = 0
            
            # Get interaction success rate
            try:
                cursor.execute('''
                    SELECT COUNT(*) FROM interaction_history WHERE success = 1
                ''')
                successful = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM interaction_history
                ''')
                total = cursor.fetchone()[0]
                
                stats["interaction_success_rate"] = successful / total if total > 0 else 0
            except sqlite3.OperationalError:
                stats["interaction_success_rate"] = 0
            
            self._close_connection(conn)
            return stats
    
    def __del__(self):
        """Clean up the in-memory connection when object is destroyed"""
        if self._connection:
            self._connection.close()