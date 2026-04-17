#pragma once

#include <QString>
#include <QVector>
#include "track.h"

namespace metatag {

class TagReader {
public:
    static Track readTrack(const QString& filePath);
    static QVector<Track> readTracks(const QVector<QString>& filePaths);
};

}