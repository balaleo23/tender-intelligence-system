import tensorflow as tf
layers = tf.keras.layers
Model = tf.keras.Model
import numpy as np
from PIL import Image
import cv2
import io

class CaptchaCNN:
    def __init__(self, num_chars=6, charset_size=62):  # A-Z, a-z, 0-9
        self.charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        assert len(self.charset) == charset_size
        self.idx_to_char = list(self.charset)
        self.char_to_idx = {c: i for i, c in enumerate(self.charset)}
        self.blank_idx = charset_size  # Blank label for CTC
        self.model = self.build_model(num_chars, charset_size + 1)  # +1 for blank
        
    def build_model(self, num_chars, charset_size):
        """Production-ready CNN for 6-char mixed case CAPTCHA"""
        input_img = layers.Input(shape=(50, 200, 1), name='image')
        
        # CNN Feature extraction
        x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(input_img)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        
        # Reshape for CTC
        # new_shape = ((x.shape[1] - 1) // 2, (x.shape[2] - 1) // 2 * x.shape[3])
        x = layers.Reshape(target_shape=(12, 50 * 128))(x)
        x = layers.Dense(num_chars + 1, activation='relu', name='dense2')(x)
        
        # CTC Loss output
        x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(128, return_sequences=True))(x)
        x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64, return_sequences=True))(x)
        
        # Output layer (62 classes: A-Z,a-z,0-9)
        output = tf.keras.layers.Dense(62, activation='softmax')(x)
        
        model = tf.keras.Model(inputs=input_img, outputs=output)
        return model
    

    # def preprocess_captcha(self, img):
        """Improve OCR accuracy for CAPTCHA images"""
        # Convert to grayscale
        img = img.convert('L')
        img_np = np.array(img)

        img_np = cv2.medianBlur(img_np, 3)
        img_np = cv2.GaussianBlur(img_np, (3, 3), 0)

        img_np = cv2.adaptiveThreshold(img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        img_np = cv2.morphologyEx(img_np, cv2.MORPH_OPEN, kernel)
        img_clean = Image.fromarray(img_np)
        # Enhance contrast
        # img = ImageEnhance.Contrast(img).enhance(2)
        
        # Apply threshold
        # img_np = np.array(img)
        # _, img_np = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # img = Image.fromarray(img_np)
        
        return img_clean
   
    def preprocess_captcha(self, pil_img):
        """Convert PIL image to CNN input format"""
        # Resize to model input: 50x200 grayscale
        # img = pil_img.convert('L')
        # img = pil_img.resize((200, 50))
        img = pil_img.convert('L')  # Grayscale
        img_np = np.array(img)
        # Noise reduction
        img_np = cv2.medianBlur(img_np, 3)
        img_np = cv2.GaussianBlur(img_np, (3, 3), 0)

        # Adaptive thresholding
        img_np = cv2.adaptiveThreshold(img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Morphology to remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        img_np = cv2.morphologyEx(img_np, cv2.MORPH_OPEN, kernel)
        # Normalize 0-1
        img_clean = Image.fromarray(img_np)
        img_resized = img_clean.resize((200, 50))  # Width 200, height 50
        
        # Normalize and add dimensions
        img_array = np.array(img_resized) / 255.0
        img_array = np.expand_dims(img_array, axis=-1)  # Add channel: (50, 200, 1)
        img_array = np.expand_dims(img_array, axis=0)   # Add batch: (1, 50, 200, 1)
        # img_array = img_array.reshape(1, 50, 200, 1)
        return img_array.astype(np.float32)
    
    def predict(self, pil_img):
        """Predict CAPTCHA text from PIL image"""
        processed_img = self.preprocess_captcha(pil_img)
        
        # Predict
        pred = self.model.predict(processed_img)
        
        # CTC Decoder (simplified)
        output_text = self.ctc_decode(pred)
        return output_text

    def ctc_decode(self, pred):
        """Decode CTC output to text"""
        # Simple argmax decoder
        pred_indices = np.argmax(pred[0], axis=1)
        text_chars = []
        
        for idx in pred_indices:
            if idx > 0 and idx < len(self.char_to_idx):  # Valid char
                for char, char_idx in self.char_to_idx.items():
                    if char_idx == idx:
                        text_chars.append(char)
                        break
        
        return ''.join(text_chars[:6])  # Max 6 chars
