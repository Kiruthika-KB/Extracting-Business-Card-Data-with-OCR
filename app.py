import streamlit as st
import mysql.connector
from PIL import Image
import io
import re
import pytesseract

# Set the Tesseract executable path
pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Database setup
def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="business_cards_db"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS business_cards (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        company_name VARCHAR(255),
                        card_holder_name VARCHAR(255),
                        designation VARCHAR(255),
                        mobile_number VARCHAR(255),
                        email_address VARCHAR(255),
                        website_url VARCHAR(255),
                        city VARCHAR(255),
                        state VARCHAR(255),
                        pin_code VARCHAR(255),
                        card_image LONGBLOB
                    )''')
    conn.commit()
    conn.close()

# Save to database
def save_to_db(data, image):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="business_cards_db"
    )
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO business_cards 
    (company_name, card_holder_name, designation, mobile_number, 
     email_address, website_url, city, state, pin_code, card_image)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
    (data.get('company_name', ''), data.get('card_holder_name', ''), data.get('designation', ''), 
     data.get('mobile_number', ''), data.get('email_address', ''), data.get('website_url', ''), 
     data.get('city', ''), data.get('state', ''), data.get('pin_code', ''), image))
    conn.commit()
    conn.close()

# Read all records from the database and display images
def read_from_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="business_cards_db"
    )
    cursor = conn.cursor()
    cursor.execute('SELECT id, company_name, card_holder_name, designation, mobile_number, email_address, website_url, city, state, pin_code, card_image FROM business_cards')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Update record in database
def update_record(record_id, updated_data):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="business_cards_db"
    )
    cursor = conn.cursor()

    # Dynamically build the update query
    update_fields = []
    update_values = []
    for key, value in updated_data.items():
        if value:  # Only update fields with non-empty values
            # Escape column names with backticks
            column_name = f"`{key}`"
            update_fields.append(f"{column_name} = %s")
            update_values.append(value)

    if update_fields:
        update_query = f"UPDATE business_cards SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(record_id)  # Add record_id as the last value

        cursor.execute(update_query, tuple(update_values))
        conn.commit()
    conn.close()

# Delete record from database
def delete_record(record_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="business_cards_db"
    )
    cursor = conn.cursor()
    cursor.execute('DELETE FROM business_cards WHERE id=%s', (record_id,))
    conn.commit()
    conn.close()

# Regular Expressions for Extraction
def extract_fields(text):
    data = {
        "company_name": "",
        "card_holder_name": "",
        "designation": "",
        "mobile_number": "",
        "email_address": "",
        "website_url": "",
        "city": "",
        "state": "",
        "pin_code": ""
    }

    # Extract Email
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    email = re.findall(email_regex, text)
    if email:
        data["email_address"] = email[0]

    # Extract Mobile Number
    mobile_regex = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    mobile = re.findall(mobile_regex, text)
    if mobile:
        data["mobile_number"] = mobile[0]

    # Extract Website URL
    website_regex = r'(www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    website = re.findall(website_regex, text)
    if website:
        data["website_url"] = website[0]

    # Attempt to Parse Address Details
    address_regex = r'(?P<city>[A-Za-z\s]+),\s*(?P<state>[A-Za-z\s]+)\s*(?P<pin>\d{6})'
    address_match = re.search(address_regex, text)
    if address_match:
        data.update({
            "city": address_match.group("city"),
            "state": address_match.group("state"),
            "pin_code": address_match.group("pin")
        })

    # Extract Company Name, Card Holder Name, and Designation
    lines = text.splitlines()
    if lines:
        data["company_name"] = "GLOBAL INSURANCE"  # Example assumption
        data["card_holder_name"] = lines[0]  # Assuming card holder name is on the first line
        if len(lines) > 1:
            data["designation"] = lines[1]  # Assuming designation is on the second line

    return data

# Extraction function with pytesseract
def extract_text(image):
    pil_image = Image.open(image)
    text = pytesseract.image_to_string(pil_image)
    extracted_info = extract_fields(text)
    return extracted_info

# Streamlit UI
def main():
    st.title("Business Card OCR")

    # Upload image
    uploaded_image = st.file_uploader("Upload a business card", type=['jpg', 'jpeg', 'png'])
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Business Card", use_column_width=True)
        extracted_info = extract_text(uploaded_image)
        if st.button("Extract Information"):
            st.json(extracted_info)

        if st.button("Save to Database"):
            if not extracted_info:
                st.warning("No data to save!")
            else:
                image_bytes = io.BytesIO()
                image.save(image_bytes, format='PNG')
                save_to_db(extracted_info, image_bytes.getvalue())
                st.success("Saved to database successfully!")

    # View records
    if st.checkbox("View Records"):
        records = read_from_db()
        for record in records:
            st.write(f"ID: {record[0]}")
            st.write(f"Company Name: {record[1]}")
            st.write(f"Card Holder Name: {record[2]}")
            st.write(f"Designation: {record[3]}")
            st.write(f"Mobile Number: {record[4]}")
            st.write(f"Email Address: {record[5]}")
            st.write(f"Website URL: {record[6]}")
            st.write(f"City: {record[7]}")
            st.write(f"State: {record[8]}")
            st.write(f"Pin Code: {record[9]}")
            if record[10]:
                image = Image.open(io.BytesIO(record[10]))
                st.image(image, caption=f"Business Card ID: {record[0]}", use_column_width=True)

    # Update record
    if st.checkbox("Update a Record"):
        record_id = st.number_input("Enter Record ID to Update", min_value=1, step=1)
        updated_data = {
            "company_name": st.text_input("Company Name"),
            "card_holder_name": st.text_input("Card Holder Name"),
            "designation": st.text_input("Designation"),
            "mobile_number": st.text_input("Mobile Number"),
            "email_address": st.text_input("Email Address"),
            "website_url": st.text_input("Website URL"),
            "city": st.text_input("City"),
            "state": st.text_input("State"),
            "pin_code": st.text_input("Pin Code")
        }
        if st.button("Update Record"):
            update_record(record_id, updated_data)
            st.success("Record updated successfully!")

    # Delete record
    if st.checkbox("Delete a Record"):
        record_id = st.number_input("Enter Record ID to Delete", min_value=1, step=1)
        if st.button("Delete Record"):
            delete_record(record_id)
            st.success("Record deleted successfully!")

if __name__ == "__main__":
    init_db()
    main()
