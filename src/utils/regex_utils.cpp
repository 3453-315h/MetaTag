#include "regex_utils.h"
#include <QRegularExpression>
#include <QRegularExpressionMatchIterator>

namespace metatag {

QVector<QString> RegexUtils::findMatches(const QString& pattern, const QString& text)
{
    QVector<QString> matches;
    QRegularExpression re(pattern);
    if (!re.isValid())
        return matches;
    
    auto iterator = re.globalMatch(text);
    while (iterator.hasNext()) {
        auto match = iterator.next();
        matches.append(match.captured(0));
    }
    return matches;
}

QString RegexUtils::replaceMatches(const QString& pattern, const QString& replacement, const QString& text)
{
    QRegularExpression re(pattern);
    if (!re.isValid())
        return text;
    
    return text.replace(re, replacement);
}

}