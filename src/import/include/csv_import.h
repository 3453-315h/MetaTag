#pragma once

#include <QString>
#include <QVector>
#include "track.h"

namespace metatag {

class CsvImport {
public:
    bool import(const QString& csvPath, QVector<Track>& tracks);
};

}