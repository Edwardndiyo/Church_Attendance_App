# app/models/hierarchy.py
from app.extensions import db

class State(db.Model):
    __tablename__ = 'states'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    regions = db.relationship('Region', backref='state', lazy=True)

    def __repr__(self):
        return f"<State {self.name}>"

class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    districts = db.relationship('District', backref='region', lazy=True)

    def __repr__(self):
        return f"<Region {self.name}>"

class District(db.Model):
    __tablename__ = 'districts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)

    groups = db.relationship('Group', backref='district', lazy=True)

    def __repr__(self):
        return f"<District {self.name}>"

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    old_groups = db.relationship('OldGroup', backref='group', lazy=True)

    def __repr__(self):
        return f"<Group {self.name}>"

class OldGroup(db.Model):
    __tablename__ = 'old_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    leader = db.Column(db.String(100), nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    def __repr__(self):
        return f"<OldGroup {self.name}>"
