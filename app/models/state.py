# from ..extensions import db

# class State(db.Model):
#     __tablename__ = "states"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False, unique=True)
#     code = db.Column(db.String(30), nullable=True, unique=True)
#     leader = db.Column(db.String(120), nullable=True)

#     def to_dict(self):
#         return {"id": self.id, "name": self.name, "code": self.code, "leader": self.leader}
