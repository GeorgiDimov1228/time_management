
# activate venv
python3 -m venv venv
source venv/bin/activate
#install requirements
pip3 install -r requirements.txt
deactivate



docker compose up --build


curl -X POST http://127.0.0.1:8000/recipes/ \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_name": "Test Recipe",
    "node_id": "node-123",
    "description": "A test recipe",
    "recipe_items": [
      {
        "item_id": 1,
        "required_quantity": 10,
        "node_id": "node-item-1"
      }
    ]
}'



curl -X PUT http://127.0.0.1:8000/recipes/id/3 \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_name": "Updated_Recipe",
    "node_id": "node-123",
    "description": "Updated description",
    "recipe_items": [
      {
        "item_id": 2,
        "required_quantity": 15,
        "node_id": "node-item-1-updated"
      }
    ]
}'


curl -X DELETE http://127.0.0.1:8000/recipes/id/1


curl -X GET http://127.0.0.1:8000/recipes/<recipe_name>
curl -X GET "http://127.0.0.1:8000/recipes/Updated_Recipe"

curl -X GET http://127.0.0.1:8000/recipes/
