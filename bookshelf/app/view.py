from app import app, User, Search, LoginForm, RegistrationForm, db, Author, Bookshelf, BookRateAssociation, Books, \
    WrittenByAssociation, ContainsAsscociation, Addbook, Publisher, BookRateTotal
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = Search()
    if current_user.is_authenticated is True:
        return redirect(url_for('home'))
    else:
        if form.validate_on_submit():
            result = Books.query.filter_by('%'+form.data+'%')
            return redirect(url_for('login'))
        else:
            top = Books.query.join(BookRateAssociation).all()
            x = []
            y = []
            comm = []
            for bok in top:
                s = WrittenByAssociation.query.filter_by(book_id=bok.book_id).first()
                author = Author.query.filter_by(author_id=s.author_id).first()
                comments = BookRateAssociation.query.filter_by(book_id=bok.book_id).first()
                comm.append(comments.comment)
                x.append(author.author_first_name)
                y.append(author.author_last_name)
            return render_template('index.html', top=top, form=form, x=x, y=y, comm=comm)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated is True:
        return redirect(url_for('home'))
    elif form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
                return render_template('login.html', form=form)
        else:
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if current_user.is_authenticated is True:
        return redirect(url_for('home'))
    elif form.validate_on_submit():
        new_user = User(form.username.data, form.password.data, form.first_name.data,
                        form.last_name.data, form.contact.data, form.birth_date.data, form.sex.data)
        db.session.add(new_user)
        db.session.commit()
        bookshelf = Bookshelf(new_user.id,new_user.id)
        db.session.add(bookshelf)
        db.session.commit()
        login_user(new_user, remember=True)
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/home', defaults={'page_num': 1}, methods=['GET', 'POST'])
@app.route('/home/<int:page_num>', methods=['GET', 'POST'])
@login_required
def home(page_num):
    form = Search()
    if form.validate_on_submit():
        search1 = '%'+form.search.data+'%'
        book = ContainsAsscociation.query.join(Books).filter(((Books.title.like(search1)) | (
                Books.year_published.like(search1)) | (Books.types.like(search1)) | (Books.edition.like(search1)) | (
                                                                      Books.isbn.like(search1)))).paginate(page_num, 12)
        x = []
        y = []
        for bok in book.items:
            s = ContainsAsscociation.query.filter_by(book_id=bok.book_id).first()
            d = WrittenByAssociation.query.filter_by(book_id=s.book_id).first()
            x.append(s.quantity)
            y.append(d.author.author_first_name + ' ' + d.author.author_last_name)
        return render_template('homepage1.html', page_num=page_num, book=book, current_user=current_user, form=form, x=x, y=y)
    book = WrittenByAssociation.query.join(Author).paginate(page_num, 12)
    x = []
    y = []
    for bok in book.items:
        s = ContainsAsscociation.query.filter_by(book_id=bok.books.book_id).first()
        x.append(s.quantity)
        y.append(s.availability)
    return render_template('homepage.html', page_num=page_num, book=book, current_user=current_user, form=form, x=x, y=y    )


@app.route('/profile/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    form = Search()
    if user_id == current_user.id:
        return render_template('profile.html', form=form)
    else:
        user = User.query.filter_by(id=user_id).first()
        return render_template('diffprofile.html', form=form, user=user)


@app.route('/home/book/<int:book_id>/<int:page_num>', methods=['GET', 'POST'])
@login_required
def indibook(book_id, page_num):
    form = Search()
    book = ContainsAsscociation.query.filter_by(book_id=book_id).paginate(page_num, 12)
    rate = BookRateTotal.query.filter_by(bookRated=book_id).first()
    x = []
    y = []
    z = []
    for bok in book.items:
        s = User.query.filter_by(id=bok.shelf_id).first()
        x.append(s.first_name)
        y.append(s.last_name)
        z.append(s.id)
    return render_template('individualbook.html', book=book, rate=rate, form=form, book_id=book_id, x=x, y=y, z=z)


@app.route('/profile/bookshelf/<int:user_id>/<int:page_num>', methods=['GET', 'POST'])
@login_required
def bookshelf(user_id, page_num):
    form = Search()
    booksearch = Search()
    if current_user.id == user_id:
        if booksearch.validate_on_submit():
            return redirect(url_for('bookshelfsearch', user_id=current_user.id, page_num=1, searchid=booksearch.search.data))
        books = ContainsAsscociation.query.filter_by(shelf_id=user_id).paginate(page_num, 8)
        x = []
        y = []
        for bok in books.items:
            s = WrittenByAssociation.query.filter_by(book_id=bok.book_id).first()
            author = Author.query.filter_by(author_id=s.author_id).first()
            x.append(author.author_first_name)
            y.append(author.author_last_name)
        return render_template('bookshelf.html', current_user=current_user, form=form, booksearch=booksearch, books=books, x=x, y=y)
    else:
        if booksearch.validate_on_submit():
            if booksearch.validate_on_submit():
                return redirect(url_for('bookshelfsearch', user_id=user_id, page_num=1, searchid=booksearch.search.data))
        books = ContainsAsscociation.query.filter_by(shelf_id=user_id).paginate(page_num, 8)
        x = []
        y = []
        for bok in books.items:
            s = WrittenByAssociation.query.filter_by(book_id=bok.book_id).first()
            author = Author.query.filter_by(author_id=s.author_id).first()
            x.append(author.author_first_name)
            y.append(author.author_last_name)
        return render_template('diffbookshelf.html', current_user=current_user, form=form, books=books, booksearch=booksearch, user_id=user_id, x=x, y=y)


@app.route('/profile/bookshelf/<int:user_id>/<int:page_num>/<string:searchid>', methods=['GET', 'POST'])
@login_required
def bookshelfsearch(user_id, page_num, searchid):
    form = Search()
    booksearch = Search()
    if current_user.id == user_id:
        search1 = '%'+searchid+'%'
        books = ContainsAsscociation.query.join(Books).filter(
            (ContainsAsscociation.shelf_id == current_user.id) & ((Books.title.like(search1)) | (
             Books.year_published.like(search1)) | (Books.types.like(search1)) | (Books.edition.like(search1)) | (
             Books.isbn.like(search1)))).paginate(page_num, 8)
        x = []
        y = []
        for p in books.items:
            s = WrittenByAssociation.query.filter_by(book_id=p.book_id).first()
            author = Author.query.filter_by(author_id=s.author_id).first()
            x.append(author.author_first_name)
            y.append(author.author_last_name)
        return render_template('bookshelfresult.html', current_user=current_user, form=form, search1=search1,
                               books=books, x=x, y=y, booksearch=booksearch)
    else:
        search1 = '%' + searchid + '%'
        books = ContainsAsscociation.query.join(Books).filter(
            (ContainsAsscociation.shelf_id == user_id) & ((Books.title.like(search1)) | (
                Books.year_published.like(search1)) | (Books.types.like(search1)) | (Books.edition.like(search1)) | (
                                                                      Books.isbn.like(search1)))).paginate(page_num, 8)
        x = []
        y = []
        for p in books.items:
            s = WrittenByAssociation.query.filter_by(book_id=p.book_id).first()
            author = Author.query.filter_by(author_id=s.author_id).first()
            x.append(author.author_first_name)
            y.append(author.author_last_name)
        return render_template('diffbookshelfresult.html', current_user=current_user, form=form, search1=search1,
                               books=books, x=x, y=y, booksearch=booksearch, user_id=user_id)


@app.route('/profile/rate_and_comment', methods=['GET', 'POST'])
@login_required
def ratencomm():
    form = Search()
    return render_template('commNrating.html', current_user=current_user, form=form)


@app.route('/notification', methods=['GET', 'POST'])
@login_required
def notif():
    form = Search()
    return render_template('notif.html', form=form)


@app.route('/profile/bookshelf/delete/<int:book_id>', methods=['GET', 'POST'])
@login_required
def delbook(book_id):
        avail = ContainsAsscociation.query.filter(ContainsAsscociation.book_id == book_id).first()
        availDelete = int(avail.quantity)
        avail.quantity = availDelete - 1
        db.session.commit()
        if avail.quantity <= 0:
            avail.availability = 'NO'
            db.session.commit()
        return redirect(url_for('bookshelf', user_id=current_user.id, page_num=1))


@app.route('/profile/bookshelf/add', methods=['GET', 'POST'])
@login_required
def addbook():
    form = Addbook()
    if form.validate_on_submit():
        titleNew = form.title.data
        yearNew = form.year.data
        typeNew = form.type.data
        editionNew = form.edition.data
        isbnNew = form.isbn.data
        publisherNew = form.publisher.data
        authorFirstNew = form.author_firstname.data
        authorLastNew = form.author_lastname.data
        pub = '%' + str(publisherNew) + '%'
        books = Books.query.filter((Books.title == titleNew) & (Books.edition == editionNew) & (Books.year_published == yearNew) & (
            Books.isbn == isbnNew)).first()
        publishers = Publisher.query.filter((Publisher.publisher_name.like(pub))).first()
        author = Author.query.filter((Author.author_first_name == authorFirstNew) & (Author.author_last_name == authorLastNew)).first()
        if (books is None) or (publishers is None) or (author is None):
            if publishers is None:
                pubbook = Publisher(publisherNew)
                db.session.add(pubbook)
                db.session.commit()
                pub_id = Publisher.query.filter((Publisher.publisher_name == publisherNew)).first()
                if author is None:
                    authbook = Author(authorFirstNew, authorLastNew)
                    db.session.add(authbook)
                    db.session.commit()
                elif author is not None:
                    auth_id = Author.query.filter((Author.author_first_name == authorFirstNew) and (Author.author_last_name == authorLastNew)).first()
            elif publishers is not None:
                pub_id = Publisher.query.filter((Publisher.publisher_name == publisherNew)).first()
                if author is None:
                    authbook = Author(authorFirstNew, authorLastNew)
                    db.session.add(authbook)
                    db.session.commit()
                elif author is not None:
                    auth_id = Author.query.filter((Author.author_first_name == authorFirstNew) and (
                    Author.author_last_name == authorLastNew)).first()

            auth_id = Author.query.filter((Author.author_first_name == authorFirstNew) and (Author.author_last_name == authorLastNew)).first()

            book = Books(titleNew, editionNew, yearNew, isbnNew, typeNew, pub_id.publisher_id)
            db.session.add(book)
            db.session.commit()
            contain = ContainsAsscociation(current_user.id, book.book_id, 1, 'YES')
            db.session.add(contain)
            db.session.commit()
            written = WrittenByAssociation(auth_id.author_id, book.book_id)
            db.session.add(written)
            db.session.commit()
            return redirect(url_for('bookshelf', user_id=current_user.id, page_num=1))
        else:
            bookquantity = ContainsAsscociation.query.filter((ContainsAsscociation.shelf_id == current_user.id) & (
                                                              ContainsAsscociation.book_id == books.book_id)).first()
            if bookquantity is None:
                contain = ContainsAsscociation(current_user.id, books.book_id, 1, 'YES')
                db.session.add(contain)
                db.session.commit()
            else:
                curQuant = bookquantity.quantity
                bookquantity.quantity = int(curQuant + 1)
                db.session.commit()
            return redirect(url_for('bookshelf', user_id=current_user.id, page_num=1))
    return render_template('addbook.html', form=form)


@app.route('/rateBook/<int:book_id>', methods=['POST', 'GET'])
@login_required
def ratebook(book_id):
    rate = request.form['rateUser']
    rateOld = BookRateAssociation.query.filter((BookRateAssociation.user_id == current_user.id) & (BookRateAssociation.book_id == book_id)).first()
    if rateOld is not None:
        rateOld.rating = rate
        db.session.commit()

        totOld = BookRateTotal.query.filter(BookRateTotal.bookRated == book_id).first()
        if totOld is not None:
            rateTot = BookRateAssociation.query.filter(BookRateAssociation.book_id == book_id)
            x = 0
            count = 0
            for p in rateTot:
                r = int(p.rating)
                x = float(x + r)
                count = float(count + 1)

            totRate = float(x / count)
            totOld.totalRate = totRate
            db.session.commit()
        else:
            rateTot = BookRateAssociation.query.filter(BookRateAssociation.book_id == book_id)

            x = 0
            count = 0
            for p in rateTot:
                r = int(p.rating)
                x = float(x + r)
                count = float(count + 1)

            totRate = float(x / count)

            newRateTot = BookRateTotal(current_user.id, book_id, totRate)
            db.session.add(newRateTot)
            db.session.commit()
        return redirect(url_for('indibook', book_id=book_id, page_num=1))
    else:
        newRater = BookRateAssociation(current_user.id, book_id, rate)
        db.session.add(newRater)
        db.session.commit()

        totOld = BookRateTotal.query.filter(BookRateTotal.bookRated == book_id).first()
        if totOld is not None:
            rateTot = BookRateAssociation.query.filter(BookRateAssociation.book_id == book_id)

            x = 0
            count = 0
            for p in rateTot:
                r = int(p.rating)
                x = float(x + r)
                count = float(count + 1)

            totRate = float(x / count)
            totOld.totalRate = totRate
            db.session.commit()
        else:
            rateTot = BookRateAssociation.query.filter(BookRateAssociation.book_id == book_id)

            x = 0
            count = 0
            for p in rateTot:
                r = int(p.rating)
                x = float(x + r)
                count = float(count + 1)

            totRate = float(x / count)

            newRateTot = BookRateTotal(current_user.id, book_id, totRate)
            db.session.add(newRateTot)
            db.session.commit()
    return redirect(url_for('indibook', book_id=book_id, page_num=1))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
