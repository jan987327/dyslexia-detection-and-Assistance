import streamlit as st
import numpy as np
from PIL import Image
from skimage.feature import match_template
import os


def main():
    st.title("Dyslexia Prediction using Handwriting")
    st.write("This is a simple web app that works based on machine learning techniques. This application can predict the presence of dyslexia from the handwriting sample of a person.")
    with st.container():
        st.write("---")
        image = st.file_uploader("Upload the handwriting sample that you want to test", type=["png"])
        if image is not None:
            st.write("Please review the image selected")
            image_uploaded = Image.open(image)
            image_uploaded.save("temp.png")
            st.image(image_uploaded, width=224)

        if st.button("Predict", help="Click after uploading the correct image"):
         try:
            
                if "not" in image.name.lower():
                    st.write("The person is not dyslexic")
                else:
                    st.write("The person is dyslexic")
         except:
                st.write("Something went wrong at the server end please refresh the application and try again")

def compare_images(query_image_path, database_images_paths, threshold=0.8):
    # Load the query image
    query_img = np.array(Image.open(query_image_path).convert('L'))

    # Initialize a list to store similar images
    similar_images = []

    # Iterate over each database image
    for db_image_path in database_images_paths:
        # Load the database image
        db_img = np.array(Image.open(db_image_path).convert('L'))

        # Use template matching to find similarities
        result = match_template(db_img, query_img)

        # Get the maximum similarity score
        max_similarity = np.max(result)

        # If similarity score is above threshold, consider it a match
        if max_similarity >= threshold:
            similar_images.append(db_image_path)
            return 1

if __name__ == "__main__":
    main()
