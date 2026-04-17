#include "cover_finder.h"
#include "musicbrainz_lookup.h"
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QUrlQuery>
#include <QDebug>
#include <QImage>
#include <QSslError>

namespace metatag {

CoverFinder::CoverFinder(QObject *parent)
    : QObject(parent)
{
}

void CoverFinder::fetchCover(const QString& artist, const QString& album)
{
    // First, get MusicBrainz release ID
    MusicBrainzLookup *lookup = new MusicBrainzLookup(this);
    connect(lookup, &MusicBrainzLookup::releasesFetched, this, [this](const QVector<QString>& releaseIds) {
        if (releaseIds.isEmpty()) {
            emit fetchError("No releases found for artist/album");
            return;
        }
        QString releaseId = releaseIds.first();
        fetchCoverArt(releaseId);
    });
    connect(lookup, &MusicBrainzLookup::lookupError, this, [this](const QString& error) {
        emit fetchError("MusicBrainz lookup failed: " + error);
    });
    lookup->lookupRelease(artist, album);
}

void CoverFinder::fetchCoverArt(const QString& releaseId)
{
    QNetworkAccessManager *nam = new QNetworkAccessManager(this);
    QUrl url(QString("https://coverartarchive.org/release/%1").arg(releaseId));
    QNetworkRequest request(url);
    request.setRawHeader("User-Agent", "MetaTag/1.0 (https://github.com/metatag)");
    request.setRawHeader("Accept", "application/json");
    request.setTransferTimeout(10000); // 10 seconds
    
    QNetworkReply *reply = nam->get(request);
    connect(reply, &QNetworkReply::sslErrors, this, [reply](const QList<QSslError> &errors) {
        QList<QSslError> ignorableErrors;
        for (const QSslError &error : errors) {
            // Only ignore self-signed certificates for development/testing
            if (error.error() == QSslError::SelfSignedCertificate ||
                error.error() == QSslError::SelfSignedCertificateInChain) {
                ignorableErrors.append(error);
            }
        }
        if (ignorableErrors.size() == errors.size()) {
            qWarning() << "Ignoring self-signed certificate errors:" << ignorableErrors;
            reply->ignoreSslErrors(ignorableErrors);
        } else {
            qWarning() << "SSL errors occurred and will not be ignored:" << errors;
        }
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply->error() != QNetworkReply::NoError) {
            emit fetchError("Cover Art Archive request failed: " + reply->errorString());
            reply->deleteLater();
            return;
        }
        
        QByteArray data = reply->readAll();
        reply->deleteLater();
        
        QJsonDocument doc = QJsonDocument::fromJson(data);
        if (doc.isNull()) {
            emit fetchError("Failed to parse Cover Art Archive JSON");
            return;
        }
        
        QJsonObject root = doc.object();
        QJsonArray images = root["images"].toArray();
        QString imageUrl;
        for (const QJsonValue& val : images) {
            QJsonObject imgObj = val.toObject();
            bool isFront = imgObj["front"].toBool();
            if (isFront) {
                imageUrl = imgObj["image"].toString();
                break;
            }
        }
        
        // If no front image, take first image
        if (imageUrl.isEmpty() && !images.isEmpty()) {
            QJsonObject imgObj = images.first().toObject();
            imageUrl = imgObj["image"].toString();
        }
        
        if (imageUrl.isEmpty()) {
            emit fetchError("No cover art found");
            return;
        }
        
        downloadImage(imageUrl);
    });
}

void CoverFinder::downloadImage(const QString& url)
{
    QNetworkAccessManager *nam = new QNetworkAccessManager(this);
    QNetworkRequest request(url);
    request.setRawHeader("User-Agent", "MetaTag/1.0 (https://github.com/metatag)");
    request.setTransferTimeout(10000); // 10 seconds
    
    QNetworkReply *reply = nam->get(request);
    connect(reply, &QNetworkReply::sslErrors, this, [reply](const QList<QSslError> &errors) {
        QList<QSslError> ignorableErrors;
        for (const QSslError &error : errors) {
            // Only ignore self-signed certificates for development/testing
            if (error.error() == QSslError::SelfSignedCertificate ||
                error.error() == QSslError::SelfSignedCertificateInChain) {
                ignorableErrors.append(error);
            }
        }
        if (ignorableErrors.size() == errors.size()) {
            qWarning() << "Ignoring self-signed certificate errors:" << ignorableErrors;
            reply->ignoreSslErrors(ignorableErrors);
        } else {
            qWarning() << "SSL errors occurred and will not be ignored:" << errors;
        }
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply->error() != QNetworkReply::NoError) {
            emit fetchError("Image download failed: " + reply->errorString());
            reply->deleteLater();
            return;
        }
        
        QByteArray data = reply->readAll();
        reply->deleteLater();
        
        QImage image;
        if (!image.loadFromData(data)) {
            emit fetchError("Failed to load image data");
            return;
        }
        
        emit coverFetched(image);
    });
}



QImage CoverFinder::downloadImage(const QString& url)
{
    QNetworkAccessManager nam;
    QNetworkRequest request(url);
    request.setRawHeader("User-Agent", "MetaTag/1.0 (https://github.com/metatag)");
    request.setTransferTimeout(10000); // 10 seconds
    
    QNetworkReply *reply = nam.get(request);
    QObject::connect(reply, &QNetworkReply::sslErrors, [reply](const QList<QSslError> &errors) {
        qWarning() << "SSL errors occurred:" << errors;
        reply->ignoreSslErrors();
    });
    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();
    
    if (reply->error() != QNetworkReply::NoError) {
        qWarning() << "Image download failed:" << reply->errorString();
        reply->deleteLater();
        return QImage();
    }
    
    QByteArray data = reply->readAll();
    reply->deleteLater();
    
    QImage image;
    if (!image.loadFromData(data)) {
        qWarning() << "Failed to load image data";
        return QImage();
    }
    
    return image;
}

}