from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

def setup_db(app):
    # app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(250), nullable=True)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250), nullable=True)
    genres = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue',
                            lazy=True, cascade='all, delete-orphan')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist',
                            lazy=True, cascade='all, delete-orphan')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(250), nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250), nullable=True)


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"))
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"))
