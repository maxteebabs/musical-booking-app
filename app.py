# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request,\
    Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from models import setup_db, Venue, Show, Artist
from seed import seed_data

current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
setup_db(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)


# ----------------------------------------------------------------------------#
# Seed.
@manager.command
def seed():
    seed_data(db)
# ----------------------------------------------------------------------------#

# TODO: connect to a local postgresql database
# app.config['SQLALCHEMY_DATABASE_URI'] = '

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    venues = Venue.query.order_by(db.desc(Venue.id)).limit(10).all()
    artists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    cities = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()
    data = []
    venues = Venue.query.all()
    for city in cities:
        venues = db.session.query(Venue.id, Venue.name).filter(
            Venue.city == city[0], Venue.state == city[1]).all()
        data.append({
            "city": city[0],
            "state": city[1],
            "venues": venues,
            "num_upcoming_shows": Show.query.filter(
                Show.start_time > current_time).count()
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with
    # partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop"
    # and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    data = []
    for venue in venues:
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": Show.query.filter(
                Show.start_time > current_time)
            .filter(Show.venue_id == venue.id).count()
        })

    response = {
        "count": len(venues),
        "data": data
    }

    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter_by(id=venue_id).first_or_404()

    past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
        filter(
            Show.start_time < current_time,
            Show.venue_id == venue.id,
            Show.artist_id == Artist.id
        ).all()

    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
        filter(
            Show.start_time > current_time,
            Show.venue_id == venue.id,
            Show.artist_id == Artist.id
    ).all()

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(","),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [{
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in past_shows],
        "upcoming_shows": [{
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
    #  data = list(filter(
    # lambda d: d['id'] == venue_id,
    # [data1, data2, data3]))[0]
    return render_template(
        'pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    message = ''
    try:
        form = VenueForm(request.form)
        genres = form.genres.data
        genres = ','.join([str(genre) for genre in genres])

        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            website=form.website.data,
            image_link=form.image_link.data,
            genres=genres,
            seeking_talent=bool(form.seeking_talent.data),
            seeking_description=form.seeking_description.data,
            facebook_link=form.facebook_link.data
        )
        db.session.add(venue)
        db.session.commit()
        message = 'Venue ' + form.name.data + ' was successfully listed!'
    except:
        db.session.rollback()
        print(sys.exc_info())
        message = 'An error occurred. Venue ' + \
            request.form.get('name') + ' could not be listed.'
    finally:
        db.session.close()

    # on successful db insert, flash success
    flash(message)
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' +
    # data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle
    #  cases where the session commit could fail.
    message = ""
    try:
        venue = Venue.query.get(venue_id)
        if not venue:
            abort(404)
        name = venue.name()
        db.session.delete(venue)
        db.session.commit()
        message = f'Venue {name} was successfully deleted!'
    except:
        db.session.rollback()
        message = "An error occured. venue could not be deleted"
        print(sys.exc_info())
        abort(500)
    finally:
        db.session.close()
    flash(message)
    # BONUS CHALLENGE: Implement a button to
    # delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the
    # db then redirect the user to the homepage
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.with_entities(Artist.id, Artist.name).all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with
    # partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals",
    # "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {}
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter(
                Show.start_time > current_time)
            .filter(Show.artist_id == artist.id).count()
        })
    response = {
        "count": len(artists),
        "data": data
    }

    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.get(artist_id)
    if not artist:
        abort(404)

    past_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
        filter(
            Show.start_time < current_time,
            Show.venue_id == Venue.id,
            Show.artist_id == artist.id
    ).all()

    upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
        filter(
            Show.start_time > current_time,
            Show.venue_id == Venue.id,
            Show.artist_id == artist.id
    ).all()

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": ["Rock n Roll"],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in past_shows],
        "upcoming_shows": [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    # data = list(filter(
    # lambda d: d['id'] == artist_id,
    # [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    data = Artist.query.get(artist_id)
    if not data:
        abort(404)
    artist = {
        "id": data.id,
        "name": data.name,
        "genres": ["Rock n Roll"],
        "city": data.city,
        "state": data.state,
        "phone": data.phone,
        "website": data.website,
        "facebook_link": data.facebook_link,
        "seeking_venue": data.seeking_venue,
        "seeking_description": data.seeking_description,
        "image_link": data.image_link,
    }

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    message = ''
    try:
        artist = Artist.query.get(artist_id)
        if not artist:
            abort(404)

        form = ArtistForm(request.form)
        genres = form.data.genres
        genres = ','.join([str(genre) for genre in genres])

        # convert genres to string
        artist.name = form.name.data,
        artist.city = form.city.data,
        artist.state = form.state.data,
        artist.genres = genres,
        artist.facebook_link = form.facebook_link.data,
        artist.website = form.website.data,
        artist.seeking_venue = bool(form.seeking_venue.data),
        artist.seeking_description = form.seeking_description.data,
        artist.image_link = form.image_link.data

        db.session.update(artist)
        db.session.commit()
        message = 'Artist ' + form.name.data + ' was successfully updated!'
    except:
        db.session.rollback()
        print(sys.exc_info())
        message = 'An error occurred. Artist ' + \
            request.form.get('name') + ' could not be updated.'
    finally:
        db.session.close()

    return redirect(url_for('show_artist'))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    data = Venue.query.get(artist_id)
    if not data:
        abort(404)

    venue = {
        "id": data.id,
        "name": data.name,
        "genres": data.genres.split(","),
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "phone": data.phone,
        "website": data.website,
        "facebook_link": data.facebook_link,
        "seeking_talent": data.seeking_talent,
        "seeking_description": data.seeking_description,
        "image_link": data.image_link,
    }

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    message = ''
    try:
        venue = Venue.query.get(venue_id)
        if not venue:
            abort(404)

        form = VenueForm(request.form)
        genres = form.genres.data
        genres = ','.join([str(genre) for genre in genres])
        # convert genres to string
        venue.name = form.name.data,
        venue.city = form.city.data,
        venue.state = form.state.data,
        venue.genres = genres,
        venue.facebook_link = form.facebook_link.data,
        venue.phone = form.phone.data,
        venue.website = form.website.data,
        venue.image_link = form.image_link.data,
        venue.seeking_talent = bool(form.seeking_talent.data),
        venue.seeking_description = form.seeking_description.data,

        db.session.update(venue)
        db.session.commit()
        message = 'Venue ' + name + ' was successfully updated!'
    except:
        db.session.rollback()
        print(sys.exc_info())
        message = 'An error occurred. Venue ' + \
            request.form.get('name') + ' could not be updated.'
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    message = ''
    try:
        form = ArtistForm(request.form)

        genres = form.genres.data
        genres = ','.join([str(genre) for genre in genres])
        # convert genres to string
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            genres=genres,
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            seeking_venue=bool(form.seeking_venue.data),
            seeking_description=form.seeking_description.data,
            image_link=form.image_link.data
        )

        db.session.add(artist)
        db.session.commit()
        message = 'Artist ' + name + ' was successfully listed!'
    except:
        db.session.rollback()
        print(sys.exc_info())
        message = 'An error occurred. Artist ' + \
            request.form.get('name') + ' could not be listed.'
    finally:
        db.session.close()

    # on successful db insert, flash success
    flash(message)

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' +
    # data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based
    #  on number of upcoming shows per venue.
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db,
    # upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    message = ''
    data = {}
    try:
        form = ShowForm(request.form)
        show = Show(
            venue_id=form.venue_id.data,
            artist_id=form.artist_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
        message = 'Show was successfully listed!'
    except:
        db.session.rollback()
        print(sys.exc_info())
        message = 'An error occurred. Show could not be listed.'
    finally:
        db.session.close()

    # on successful db insert, flash success
    flash(message)
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: \
            %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    # manager.run()
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
