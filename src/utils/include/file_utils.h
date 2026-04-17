#pragma once

#include <QString>
#include <QVector>

namespace metatag {

class FileUtils {
public:
    static bool safeMove(const QString& src, const QString& dst);
    static bool safeCopy(const QString& src, const QString& dst);
    static bool safeDelete(const QString& path);
    static QVector<QString> findAudioFiles(const QString& directory);
};

}