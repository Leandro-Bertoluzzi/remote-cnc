from database.base import Session
from database.models import Material, Tool, User
from utils.security import hash_password

# Database initial data
INITIAL_DATA = [
    # Materials
    Material('Fibrofácil 3mm', 'Plancha de madera delgada.'),
    Material('PCB FR4', 'Placa de circuito impreso de fibra de vidrio.'),
    # Tools
    Tool('Mecha HSS 5mm', 'Mecha de acero rápido para taladrado de madera y materiales blandos.'),
    Tool('Fresa plana 6mm', 'Fresa plana, para trabajos de desbaste en madera.'),
    # Users
    User('Admin', 'admin@test.com', hash_password('password'), 'admin')
]


def seed_tables():
    """This method receives a table, a connection and inserts data to that table."""
    session = Session()
    for item in INITIAL_DATA:
        session.add(item)
    session.commit()


if __name__ == "__main__":
    seed_tables()
