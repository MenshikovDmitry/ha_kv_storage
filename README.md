# KV Store

A custom integration for Home Assistant that provides a persistent key-value store, accessible via sensors and services. Useful for storing arbitrary data, codes, or state between automations and scripts. I personally use it to store IR codes for the aircons, which normally are longer then 255 characters and can not be stored as an entity state.

## Features
- Store and retrieve key-value pairs in named stores
- Each store is represented as a sensor entity
- Key-value pairs are stored as attributes of the entity
- Set and delete values via Home Assistant services
- Data is persisted in JSON files in your config/.storage directory
- Supports multiple independent stores

## Installation
1. Copy the `kv_store` folder to `config/custom_components/` in your Home Assistant config directory.
2. Restart Home Assistant.
3. Add the following to your `configuration.yaml`:
   ```yaml
   kv_store:
     - my_store1
     - my_store2
   ```
4. Restart Home Assistant again.

## HACS Installation (Recommended)
- Add this repository as a custom repository in HACS (category: Integration).
- Install via HACS and restart Home Assistant.

## Usage
### Services
- `kv_store.set`: Set a key-value pair in a store. Overwrites existing value if presented
- `kv_store.delete`: Delete a key from a store

#### Example service call (set):
```yaml
service: kv_store.set
data:
  key: my_key
  value: my_value
  store_name: my_store1
```

#### Example service call (delete):
```yaml
service: kv_store.delete
data:
  key: my_key
  store_name: my_store1
```

### Sensors
Each store is available as a sensor entity, e.g. `sensor.my_store1`. The sensor's attributes contain all key-value pairs in the store.

## License
MIT
