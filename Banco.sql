CREATE DATABASE AppFit;
USE AppFit;

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nm_usuario VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    altura FLOAT NOT NULL,
    peso DECIMAL(5,2) NOT NULL,
    idade INT NOT NULL,
    sexo varchar(20)
);

CREATE TABLE ficha (
    id_ficha INT AUTO_INCREMENT PRIMARY KEY,
    exercicio VARCHAR(100) NOT NULL,
    atv_peso DECIMAL(5,2),
    repeticoes INT,
    tempo date,
    gasto_calorico FLOAT NOT NULL,
    id_usuario INT,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

create table atv_cardio(

	cardio_id int auto_increment primary key,
    tempo_atv time,
    ritimo_medio time,
    id_usuario int,
    foreign key (id_usuario) references usuario (id_usuario)
    
);

CREATE TABLE historico (
    id_historico INT AUTO_INCREMENT PRIMARY KEY,
    dia DATETIME NOT NULL,
    id_ficha INT,
    id_usuario INT,
    FOREIGN KEY (id_ficha) REFERENCES ficha(id_ficha),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);
