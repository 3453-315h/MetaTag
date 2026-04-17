#pragma once

#include <QString>
#include <QVector>
#include "track.h"

namespace metatag {

class iTunesSync {
public:
    bool importLibrary(const QString& xmlPath, QVector<Track>& tracks);
    bool exportChanges(const QVector<Track>& tracks);
};

}