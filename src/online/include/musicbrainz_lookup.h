#pragma once

#include <QObject>
#include <QString>
#include <QVector>

namespace metatag {

class MusicBrainzLookup : public QObject {
    Q_OBJECT
public:
    explicit MusicBrainzLookup(QObject *parent = nullptr);
    void lookupRelease(const QString& artist, const QString& album);

signals:
    void releasesFetched(const QVector<QString>& releases);
    void lookupError(const QString& error);
};

}