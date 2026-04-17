#pragma once

#include <QObject>
#include <QImage>
#include <QString>

namespace metatag {

class CoverFinder : public QObject {
    Q_OBJECT
public:
    explicit CoverFinder(QObject *parent = nullptr);
    void fetchCover(const QString& artist, const QString& album);

signals:
    void coverFetched(const QImage& image);
    void fetchError(const QString& error);

private:
    void fetchCoverArt(const QString& releaseId);
    void downloadImage(const QString& url);
};

}