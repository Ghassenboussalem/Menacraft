import numpy as np
import pandas as pd
from scipy.stats import entropy
from datetime import datetime

class FeatureExtractor:
    """Extract bot detection features across four signal categories"""
    
    def __init__(self):
        pass
    
    # ===== PROFILE SIGNALS =====
    def calculate_username_entropy(self, username):
        """Calculate character entropy - random usernames have higher entropy"""
        if not username or len(username) == 0:
            return 0
        char_counts = {}
        for char in username.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        probs = [count / len(username) for count in char_counts.values()]
        return entropy(probs, base=2)
    
    def extract_profile_signals(self, account_data):
        """Extract profile-based bot signals"""
        features = {}
        
        # Username analysis
        username_length = account_data.get('username_length', 0)
        username_digit_count = account_data.get('username_digit_count', 0)
        
        features['username_length'] = username_length
        features['username_digit_ratio'] = username_digit_count / max(1, username_length)
        features['has_profile_pic'] = account_data.get('user_has_profil_pic', 
                                                       account_data.get('user_has_profile_pic', 0))
        features['bio_length'] = account_data.get('user_biography_length', 0)
        features['is_private'] = account_data.get('user_is_private', 0)
        
        # Red flags
        features['no_bio'] = 1 if features['bio_length'] == 0 else 0
        features['no_profile_pic'] = 1 - features['has_profile_pic']
        features['high_digit_username'] = 1 if features['username_digit_ratio'] > 0.3 else 0
        
        return features
    
    # ===== ACTIVITY SIGNALS =====
    def extract_activity_signals(self, account_data):
        """Extract activity pattern signals"""
        features = {}
        
        media_count = account_data.get('user_media_count', 0)
        features['media_count'] = media_count
        
        # Analyze posting patterns if timestamps available
        upload_times = account_data.get('media_upload_times', account_data.get('mediaUpload_times', []))
        
        if upload_times and len(upload_times) > 1:
            # Convert to sorted array
            times = sorted(upload_times)
            intervals = np.diff(times)
            
            if len(intervals) > 0:
                # Detect regular posting intervals (bot behavior)
                features['avg_post_interval'] = np.mean(intervals)
                features['std_post_interval'] = np.std(intervals)
                features['post_interval_regularity'] = features['std_post_interval'] / max(1, features['avg_post_interval'])
                
                # Burst detection - many posts in short time
                hour_intervals = intervals / 3600  # Convert to hours
                features['burst_posts'] = np.sum(hour_intervals < 1)  # Posts within 1 hour
            else:
                features['avg_post_interval'] = 0
                features['std_post_interval'] = 0
                features['post_interval_regularity'] = 0
                features['burst_posts'] = 0
        else:
            features['avg_post_interval'] = 0
            features['std_post_interval'] = 0
            features['post_interval_regularity'] = 0
            features['burst_posts'] = 0
        
        return features
    
    # ===== ENGAGEMENT SIGNALS =====
    def extract_engagement_signals(self, account_data):
        """Extract engagement-based bot signals"""
        features = {}
        
        follower_count = account_data.get('user_follower_count', 0)
        following_count = account_data.get('user_following_count', 0)
        media_count = account_data.get('user_media_count', 0)
        
        features['follower_count'] = follower_count
        features['following_count'] = following_count
        features['follower_following_ratio'] = follower_count / max(1, following_count)
        
        # Engagement rate calculation
        media_likes = account_data.get('media_like_numbers', account_data.get('mediaLikeNumbers', []))
        media_comments = account_data.get('media_comment_numbers', account_data.get('mediaCommentNumbers', []))
        
        if media_likes and len(media_likes) > 0:
            avg_likes = np.mean(media_likes)
            features['avg_likes_per_post'] = avg_likes
            features['engagement_rate'] = (avg_likes / max(1, follower_count)) * 100
        else:
            features['avg_likes_per_post'] = 0
            features['engagement_rate'] = 0
        
        if media_comments and len(media_comments) > 0:
            features['avg_comments_per_post'] = np.mean(media_comments)
        else:
            features['avg_comments_per_post'] = 0
        
        # Red flags
        # Only flag low engagement if we actually have engagement data
        # If engagement_rate is 0 and we have no likes data, it means data is missing, not that engagement is low
        media_likes = account_data.get('media_like_numbers', account_data.get('mediaLikeNumbers', []))
        has_engagement_data = media_likes and len(media_likes) > 0
        
        if has_engagement_data:
            features['low_engagement'] = 1 if features['engagement_rate'] < 1 else 0
        else:
            features['low_engagement'] = 0  # Don't penalize missing data
        
        # Suspicious follower ratio: following way more than followers
        features['suspicious_follower_ratio'] = 1 if features['follower_following_ratio'] < 0.1 and following_count > 1000 else 0
        
        # High following is suspicious if combined with low followers
        if follower_count < 500 and following_count > 2000:
            features['high_following'] = 1
        else:
            features['high_following'] = 0
        
        return features
    
    # ===== CONTENT SIGNALS =====
    def extract_content_signals(self, account_data):
        """Extract content-based bot signals"""
        features = {}
        
        # Hashtag analysis
        hashtag_numbers = account_data.get('media_hashtag_numbers', account_data.get('mediaHashtagNumbers', []))
        
        if hashtag_numbers and len(hashtag_numbers) > 0:
            features['avg_hashtags_per_post'] = np.mean(hashtag_numbers)
            features['max_hashtags'] = np.max(hashtag_numbers)
            features['excessive_hashtags'] = 1 if features['avg_hashtags_per_post'] > 20 else 0
        else:
            features['avg_hashtags_per_post'] = 0
            features['max_hashtags'] = 0
            features['excessive_hashtags'] = 0
        
        # Location info
        has_location = account_data.get('media_has_location_info', account_data.get('mediaHasLocationInfo', []))
        if has_location and len(has_location) > 0:
            features['location_usage_rate'] = np.mean(has_location)
        else:
            features['location_usage_rate'] = 0
        
        # External URL presence
        features['has_external_url'] = account_data.get('user_has_external_url', 
                                                        account_data.get('user_has_url', 0))
        
        return features
    
    def extract_all_features(self, account_data):
        """Extract all features for an account"""
        all_features = {}
        
        all_features.update(self.extract_profile_signals(account_data))
        all_features.update(self.extract_activity_signals(account_data))
        all_features.update(self.extract_engagement_signals(account_data))
        all_features.update(self.extract_content_signals(account_data))
        
        return all_features
    
    def extract_features_from_dataframe(self, df):
        """Extract features for all accounts in a dataframe"""
        feature_list = []
        
        for idx, row in df.iterrows():
            features = self.extract_all_features(row.to_dict())
            feature_list.append(features)
        
        return pd.DataFrame(feature_list)
