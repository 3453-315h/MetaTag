#include "string_utils.h"
#include <QStringList>
#include <QRegularExpression>

namespace metatag {

QString StringUtils::toTitleCase(const QString& str)
{
    if (str.isEmpty())
        return str;
    
    QStringList words = str.split(' ', Qt::SkipEmptyParts);
    for (auto& word : words) {
        if (!word.isEmpty()) {
            word = word.front().toUpper() + word.mid(1).toLower();
        }
    }
    return words.join(' ');
}

QString StringUtils::toSentenceCase(const QString& str)
{
    if (str.isEmpty())
        return str;
    
    QString result = str;
    result[0] = result[0].toUpper();
    return result;
}

QString StringUtils::toUpper(const QString& str)
{
    return str.toUpper();
}

QString StringUtils::toLower(const QString& str)
{
    return str.toLower();
}

}