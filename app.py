from flask import Flask, request, jsonify
import pandas as pd
import yfinance as yf
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from flask_cors import CORS
from data_fetch import create_sequences

app = Flask(__name__)
CORS(app)

scaler = MinMaxScaler()


@app.route('/predict', methods=['POST'])
def predict ():
    
    try:
        data = request.json
        stock_name = data["stock_name"]
        model = tf.keras.models.load_model(f"{stock_name}_model.h5")
        days = int(data["days"])
        
        df = yf.download(stock_name, period="max", interval="1d")
        df.index = pd.to_datetime(df.index)
        
        df = df[["Adj Close"]].dropna()
        scaled_data = scaler.fit_transform(df)
        
        x_seq, _ = create_sequences(scaled_data)
        
        last_seq = x_seq[-1].reshape(1, x_seq.shape[1], x_seq.shape[2])
        
        predictions = []
        
        for _ in range(days):
            pred = model.predict(last_seq)
            # Update the sequence: remove the oldest and add the newest prediction
            # Reshape the prediction to match the shape (samples, timesteps, features)
            last_seq = np.append(last_seq[:, 1:, :], np.expand_dims(pred, axis=1), axis=1)
            
            predictions.append(pred[0, 0])
        
        predictions_rescaled = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        return jsonify({"predicted_price": predictions_rescaled.tolist()})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.after_request
def after_request (response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


if __name__ == '__main__':
    app.run(debug=True)
