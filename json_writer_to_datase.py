from loader import bot, db
import json
import logging
import xlsxwriter
import tablib
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def json_writer_to_database():
    try:
        with open('main.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Print and log the type and content of the loaded data
        logging.info(f"Data Type: {type(data)}")
        logging.info(f"Data Content: {data}")

        # Check if data is a dictionary with 'regions'
        if not isinstance(data, dict) or 'regions' not in data:
            raise ValueError("JSON data is not in the expected format")

        regions = data['regions']
        logging.info('Starting to import data...')

        for region in regions:
            region_id = region.get('id')
            region_name = region.get('name')
            if not isinstance(region_id, int) or not isinstance(region_name, str):
                raise ValueError(f"Invalid region data: {region}")

            for district in region.get('districts', []):
                district_id = district.get('id')
                district_name = district.get('name')

                if not isinstance(district_id, int) or not isinstance(district_name, str):
                    raise ValueError(f"Invalid district data: {district}")

                # Prepare data for insertion
                existing_address = db.select_address(
                    region_id=str(region_id),
                    name=district_name,
                    pk=str(district_id),
                    region_name=region_name
                )

                if not existing_address:
                    db.add_address(
                        user_id=None,
                        region_id=str(region_id),
                        name=district_name,
                        pk=str(district_id),
                        region_name=region_name
                    )
                    logging.info(f"Added address: {district_name} in region {region_name}")
                else:
                    logging.info(f"Full address record already exists for {district_name} in region {region_name}. Skipping.")

        logging.info('Data import completed.')
    except Exception as e:
        logging.error(f"Error during JSON import: {e}")



def write_to_database():
    file_name = 'users_list.xlsx'
    with open(file_name, 'rb') as f:
        data = tablib.Dataset().load(f.read(), format='xlsx')

    for row in data.dict:
        db.add_user(
            id=row['user_id'],
            fullname=row['fullname'],
            telegram_id=None,
            language='uz',
            phone=row['phone'],
            phone_number=row['phone_number'],
            manzil=row['manzil'],
            saja=row['saja'],
            sj_avia=row['sj_avia'],
            tuman=row['tuman'],
            exact_address=row['exact_address'],
            description=row['description'],
            user_id=row['user_id']
        )

    print("All users added")