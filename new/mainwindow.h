#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onSendClicked();

private:
    QTextEdit *output_text;
    QLineEdit *input_text;
    QPushButton *sendButton;
    QPushButton *clearButton;

    void appendMessage(const QString &sender, const QString &message);
    void clearChat();

    bool firstMessageSent = false;
};

#endif // MAINWINDOW_H
