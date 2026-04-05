import numpy as np
import pandas as pd
import networkx as nx

class NetworkAnalyzer:
    """Stage 4: Network analysis for bot farm detection"""
    
    def __init__(self):
        self.graph = nx.Graph()
    
    def build_follower_network(self, follower_data):
        """
        Build network graph from follower relationships
        follower_data: list of tuples (account_id, follower_id)
        """
        self.graph.add_edges_from(follower_data)
        return self.graph
    
    def detect_bot_clusters(self, bot_scores, threshold=55):
        """
        Detect clusters of suspicious accounts
        bot_scores: dict mapping account_id to bot_score
        """
        # Add bot scores as node attributes
        nx.set_node_attributes(self.graph, bot_scores, 'bot_score')
        
        # Detect communities using Louvain method (approximation with label propagation)
        try:
            communities = nx.community.label_propagation_communities(self.graph)
        except:
            # Fallback to connected components
            communities = nx.connected_components(self.graph)
        
        suspicious_clusters = []
        
        for community in communities:
            community_list = list(community)
            
            if len(community_list) < 3:
                continue
            
            # Calculate average bot score in community
            scores = [bot_scores.get(node, 0) for node in community_list if node in bot_scores]
            
            if len(scores) > 0:
                avg_score = np.mean(scores)
                bot_percentage = sum(1 for s in scores if s > threshold) / len(scores)
                
                if bot_percentage > 0.7:  # 70% of cluster flagged
                    suspicious_clusters.append({
                        'accounts': community_list,
                        'size': len(community_list),
                        'avg_bot_score': avg_score,
                        'bot_percentage': bot_percentage
                    })
        
        return suspicious_clusters
    
    def calculate_network_features(self, account_id, bot_scores):
        """Calculate network-based features for an account"""
        if account_id not in self.graph:
            return {
                'neighbor_bot_ratio': 0,
                'avg_neighbor_bot_score': 0,
                'clustering_coefficient': 0,
                'degree_centrality': 0
            }
        
        neighbors = list(self.graph.neighbors(account_id))
        
        if len(neighbors) == 0:
            neighbor_bot_ratio = 0
            avg_neighbor_score = 0
        else:
            neighbor_scores = [bot_scores.get(n, 0) for n in neighbors]
            neighbor_bot_ratio = sum(1 for s in neighbor_scores if s > 55) / len(neighbors)
            avg_neighbor_score = np.mean(neighbor_scores)
        
        return {
            'neighbor_bot_ratio': neighbor_bot_ratio,
            'avg_neighbor_bot_score': avg_neighbor_score,
            'clustering_coefficient': nx.clustering(self.graph, account_id),
            'degree_centrality': nx.degree_centrality(self.graph)[account_id]
        }
    
    def adjust_score_with_network(self, account_id, individual_score, bot_scores, weight=0.3):
        """
        Adjust individual bot score based on network context
        weight: how much network context influences final score (0-1)
        """
        network_features = self.calculate_network_features(account_id, bot_scores)
        
        # Network penalty/boost
        network_score = (
            network_features['neighbor_bot_ratio'] * 50 +
            (network_features['avg_neighbor_bot_score'] / 100) * 50
        )
        
        # Weighted combination
        final_score = (1 - weight) * individual_score + weight * network_score
        
        return final_score, network_features
    
    def get_network_statistics(self):
        """Get overall network statistics"""
        if len(self.graph) == 0:
            return {}
        
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'density': nx.density(self.graph),
            'num_components': nx.number_connected_components(self.graph)
        }
