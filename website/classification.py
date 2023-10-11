
import numpy as np
import tensorflow
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Function to get sequences


def get_sequences(tokenizer, description):
    """
    This function takes in a tokenizer and a description, converts the description into sequences using
    the tokenizer, pads the sequences to a maximum length of 13, and returns the padded sequences.
    
    :param tokenizer: The tokenizer is an object that is used to convert text into numerical sequences.
    It is typically created using the `Tokenizer` class from the `tensorflow.keras.preprocessing.text`
    module
    :param description: A list of strings representing the descriptions of some data
    :return: The function `get_sequences` returns a padded sequence of tokenized words from the input
    `description` using the provided `tokenizer`. The sequence is truncated to a maximum length of 13
    and padded with zeros at the end if necessary.
    """
    sequences = tokenizer.texts_to_sequences(description)
    padded_sequences = pad_sequences(
        sequences, truncating='post', maxlen=13, padding='post')
    return padded_sequences
# Function to classify categories
# Extract the model file


def categorise_description(model_data, description):
    """
    This function categorizes a given description using a pre-trained model and returns the predicted
    class.
    
    :param model_data: a dictionary containing the trained model, tokenizer, and index to labels mapping
    used for prediction
    :param description: A string containing a description of something that needs to be categorized
    :return: the predicted class/category of a given description based on a pre-trained model and
    associated data.
    """
    # Retrieve the model and its associated functions
    model = model_data['model']
    tokenizer = model_data['tokenizer']
    index_to_labels = model_data['index_to_labels']

    # Make the prediction
    p = model.predict(np.expand_dims(get_sequences(
        tokenizer, [description])[0], axis=0))[0]
    pred_class = index_to_labels[np.argmax(p).astype('uint8')]

    return pred_class
