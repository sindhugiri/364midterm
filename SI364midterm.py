###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import tweepy

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/sindhgirMidterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)

######################################
######## HELPER FXNS (If any) ########
######################################
    
#######################
##### TWITTER API #####
#######################

#API_key, API_secret, Access_Token, Access_Token_Secret
auth = tweepy.OAuthHandler("6fDcsj2MlIiCH126cZQEujVSS", "ejKAY9q4TeIKfUc7iVUcU8zKoMZC9FQmTpUbh9Dy7D7SF5k8fZ")
auth.set_access_token("804675986445004800-dWG0PdsYrSvPy5EhZtcdXIvJqlJKMIP", "PRbLqJFpY4vDXpY1coexFGmpFSmlfDQfXYhjfIRe0xLDs")

api = tweepy.API(auth, wait_on_rate_limit=True)

##################
##### MODELS #####
##################

class Tweet (db.Model):
    __tablename__= "tweet"
    tweetText = db.Column(db.String (280), primary_key=True)
    tweetUsername= db.Column(db.String, db.ForeignKey("account.accountUsername"))
    def __repr__(self):
        return "{} | Username: {}".format(self.tweetText, self.tweetUsername)

class Account (db.Model):
    __tablename__= "account" 
    accountUsername = db.Column(db.String (64), primary_key=True)
    accountFollowers = db.Column(db.Integer)
    accountFriends = db.Column(db.Integer)
    accounttweet_relationship = db.relationship ("Tweet", backref = "Account")
    def __repr__(self):
        return "{} | Followers: {}, Friends: {}".format(self.accountUsername, self.accountFollowers, self.accountFriends)

###################
###### FORMS ######
###################
class TweetForm(FlaskForm):
    accountpreference = StringField("Type in a user account", validators=[Required()])
    submit = SubmitField("Submit")

########################
###### VALIDATION ######
########################
    def validate_accountpreference(self,field):
        username = field.data 
        if username [0] == "@":
            raise ValidationError ("Twitter username cannot start with an @ sign")

#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/", methods=["GET", "POST"])
def index():
    form = TweetForm() 
    num_tweets=len(Tweet.query.all())
    if form.validate_on_submit():
        accountpreference = form.accountpreference.data

        public_tweets = tweepy.Cursor(api.user_timeline, screen_name=accountpreference, tweet_mode = "extended").items(3)

        for x in public_tweets: 
            tweetText = x.full_text
            accountUsername = accountpreference
            accountFollowers = x.user.followers_count
            accountFriends = x.user.friends_count
            
            account = Account.query.filter_by(accountUsername=accountpreference).first()
            if not account: 
                account=Account(accountUsername=accountpreference, accountFollowers=accountFollowers, accountFriends=accountFriends)
                db.session.add(account)
                db.session.commit()  

            tweet = Tweet.query.filter_by(tweetText=tweetText,tweetUsername=account.accountUsername).first()
            if tweet:  
                flash("Tweet exists")
                return redirect(url_for("accountassociated_tweets"))
            else: 
                tweet=Tweet(tweetText=tweetText,tweetUsername=account.accountUsername)
                db.session.add(tweet)
                db.session.commit() 
                flash ("Tweet is successfully added")
            return redirect(url_for("index"))

#PROVIDED: If the form did NOT validate / was not submitted
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html',form=form, num_tweets = num_tweets) 
#TODO 364: Add more arguments to the render_template invocation to send data to index.html

@app.route("/accountassociated_tweets")
def accountassociated_tweets():
    tweet_query=Tweet.query.all()
    associated_tweets = []
    for x in tweet_query:
        username_from_tweet= x.tweetUsername
        user_row = Account.query.filter_by(accountUsername=username_from_tweet).first()
        userrow_username = user_row.accountUsername
        associated_tweets.append((x.tweetText, userrow_username))
    return render_template("accountassociated_tweets.html",associated_tweets=associated_tweets)
    
@app.route("/account_followers")
def account_followers(): 
    account_followers=[]
    allaccounts_query=Account.query.all()
    for x in allaccounts_query: 
        account_followers.append((x.accountFollowers, x.accountUsername))
    return render_template("account_followers.html",account_followers=account_followers)
    
@app.route("/account_friends")
def account_friends(): 
    account_friends=[]
    allaccounts_query=Account.query.all()
    for x in allaccounts_query: 
        account_friends.append((x.accountFriends, x.accountUsername))
    return render_template("account_friends.html",account_friends=account_friends)

## Code to run the application...
# Put the code to do so here!
if __name__ == '__main__':
    db.create_all() 
    app.run(use_reloader=True,debug=True) 
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!