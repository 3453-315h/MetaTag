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
#include <QSslError>

namespace metatag {

MusicBrainzLookup::MusicBrainzLookup(QObject *parent)
    : QObject(parent)
{
}

void MusicBrainzLookup::lookupRelease(const QString& artist, const QString& album)
{
    if (artist.isEmpty() && album.isEmpty()) {
        emit lookupError("Artist and album cannot both be empty");
        return;
    }
    
    QNetworkAccessManager *nam = new QNetworkAccessManager(this);
    QUrl url("https://musicbrainz.org/ws/2/release/");
    QUrlQuery query;
    QStringList queryParts;
    if (!artist.isEmpty())
        queryParts.append(QString("artist:\"%1\"").arg(artist));
    if (!album.isEmpty())
        queryParts.append(QString("release:\"%1\"").arg(album));
    query.addQueryItem("query", queryParts.join(" AND "));
    query.addQueryItem("fmt", "json");
    url.setQuery(query);
    
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
            emit lookupError(reply->errorString());
            reply->deleteLater();
            return;
        }
        
        QByteArray data = reply->readAll();
        reply->deleteLater();
        
        QJsonDocument doc = QJsonDocument::fromJson(data);
        if (doc.isNull()) {
            emit lookupError("Failed to parse MusicBrainz JSON response");
            return;
        }
        
        QJsonObject root = doc.object();
        QJsonArray releasesArray = root["releases"].toArray();
        QVector<QString> releases;
        for (const QJsonValue& val : releasesArray) {
            QJsonObject releaseObj = val.toObject();
            QString id = releaseObj["id"].toString();
            if (!id.isEmpty())
                releases.append(id);
        }
        
        emit releasesFetched(releases);
    });
}

}