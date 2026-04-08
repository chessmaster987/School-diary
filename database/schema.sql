--
-- PostgreSQL database dump
--

-- Dumped from database version 15.0
-- Dumped by pg_dump version 15.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: academic_performance_ranking(date, date, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.academic_performance_ranking(start_date date, end_date date, subject_num integer, class_num integer) RETURNS TABLE(s_login character varying, s_avg_grade numeric, s_rank_avg_grade bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        student.login AS s_login,
        AVG(grade.grade) AS s_avg_grade,
        DENSE_RANK() OVER (ORDER BY AVG(grade.grade) DESC) AS s_rank_avg_grade
    FROM
        Grade
        INNER JOIN schedule ON grade.lesson_id = schedule.schedule_id
        INNER JOIN timetable ON schedule.timetable_id = timetable.timetable_id
        INNER JOIN subject ON timetable.subject_number = subject.subject_number
        INNER JOIN student ON grade.login = student.login
        INNER JOIN classes ON student.class_number = classes.class_number
    WHERE
        subject.subject_number = subject_num
        AND classes.class_number = class_num
    GROUP BY
        student.login;
END;
$$;


ALTER FUNCTION public.academic_performance_ranking(start_date date, end_date date, subject_num integer, class_num integer) OWNER TO postgres;

--
-- Name: check_schedule_conflict(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_schedule_conflict() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE 
    teacher_name TEXT; 
    conflict_count INTEGER; 
BEGIN 
    SELECT full_name INTO teacher_name FROM Teacher WHERE employee_number = (SELECT employee_number FROM timetable WHERE timetable_id = NEW.timetable_id);
    SELECT COUNT(*) INTO conflict_count FROM Schedule 
    WHERE day = NEW.day AND subject_number = NEW.subject_number 
    AND timetable_id = NEW.timetable_id AND schedule_id <> NEW.schedule_id;
    
    IF conflict_count > 0 THEN 
        RAISE EXCEPTION 'Teacher % is already scheduled for lesson % on day %', teacher_name, NEW.timetable_id, NEW.day; 
    END IF; 
    RETURN NEW; 
END; 
$$;


ALTER FUNCTION public.check_schedule_conflict() OWNER TO postgres;

--
-- Name: statistics_poor_grades(date, date, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.statistics_poor_grades(start_date date, end_date date, class_num integer) RETURNS TABLE(s_login character varying, subj_name character varying, s_num_poor_grade bigint, s_rank_poor_grade bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT  
        Student.login AS student_login, 
        Subject.subject_name AS subject, 
        COUNT(Grade.grade_number) AS marks_count, 
        DENSE_RANK() OVER (ORDER BY COUNT(Grade.grade_number) DESC) AS s_rank_poor_grade
    FROM 
        grade
        INNER JOIN student ON grade.login = student.login
        INNER JOIN schedule ON grade.lesson_id = schedule.schedule_id
        INNER JOIN timetable ON schedule.timetable_id = timetable.timetable_id
        INNER JOIN subject ON timetable.subject_number = subject.subject_number
        INNER JOIN classes ON student.class_number = classes.class_number
    WHERE 
        Grade.grade >= 1 AND Grade.grade <= 4 
        AND classes.class_number = class_num
    GROUP BY 
        Student.login, Subject.subject_name
    ORDER BY
		s_rank_poor_grade,
		Student.login, Subject.subject_name;
END;
$$;


ALTER FUNCTION public.statistics_poor_grades(start_date date, end_date date, class_num integer) OWNER TO postgres;

--
-- Name: teacher_report(integer, date, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.teacher_report(teacher_id integer, start_date date, end_date date) RETURNS TABLE(teacher_name character varying, total_grades integer, total_lessons integer, avg_grade numeric, total_classes integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
--++
	SELECT full_name INTO teacher_name FROM Teacher WHERE employee_number = teacher_id;
--++
	SELECT COUNT(*) INTO total_grades
	FROM grade g
	INNER JOIN schedule s ON g.lesson_id = s.schedule_id
	INNER JOIN timetable t ON s.timetable_id = t.timetable_id
	WHERE t.employee_number = teacher_id
	AND g.date BETWEEN start_date AND end_date;
--++
	SELECT COUNT(DISTINCT homework_number) INTO total_lessons
	FROM homework
	WHERE lesson_id IN (SELECT lesson_id FROM schedule 
					INNER JOIN schedule s ON lesson_id = s.schedule_id
					INNER JOIN timetable t ON s.timetable_id = t.timetable_id
					WHERE t.employee_number = teacher_id)
	AND date BETWEEN start_date AND end_date;
--++
	SELECT ROUND(AVG(grade)::numeric, 2) INTO avg_grade FROM grade g 
	INNER JOIN schedule s ON g.lesson_id = s.schedule_id
	INNER JOIN timetable t ON s.timetable_id = t.timetable_id
    WHERE t.employee_number = teacher_id
    AND g.date BETWEEN start_date AND end_date;
--++	    
	SELECT COUNT(DISTINCT s.class_number) INTO total_classes
	FROM Schedule s
	INNER JOIN Timetable tt ON s.timetable_id = tt.timetable_id
	INNER JOIN Teacher t ON tt.employee_number = t.employee_number
	WHERE t.employee_number = teacher_id;
    
	RETURN NEXT;
	
END;
$$;


ALTER FUNCTION public.teacher_report(teacher_id integer, start_date date, end_date date) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classes (
    class_number integer NOT NULL,
    class_name character varying(5) NOT NULL,
    CONSTRAINT classes_class_name_check CHECK (((class_name)::text ~ '^[0-9]{1,2}-?[a-zA-Zа-яА-Я]'::text))
);


ALTER TABLE public.classes OWNER TO postgres;

--
-- Name: classes_class_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.classes_class_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.classes_class_number_seq OWNER TO postgres;

--
-- Name: classes_class_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.classes_class_number_seq OWNED BY public.classes.class_number;


--
-- Name: grade; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.grade (
    grade_number integer NOT NULL,
    date date DEFAULT CURRENT_DATE NOT NULL,
    login character varying(30) NOT NULL,
    lesson_id integer NOT NULL,
    grade integer NOT NULL,
    grade_type character varying(30) NOT NULL,
    presence_mark character varying(30) NOT NULL,
    CONSTRAINT grade_grade_check CHECK (((grade >= 1) AND (grade <= 12))),
    CONSTRAINT grade_grade_type_check CHECK ((((grade_type)::text = 'homework'::text) OR ((grade_type)::text = 'test'::text) OR ((grade_type)::text = 'exam'::text))),
    CONSTRAINT grade_presence_mark_check CHECK ((((presence_mark)::text = 'YES'::text) OR ((presence_mark)::text = 'NO'::text)))
);


ALTER TABLE public.grade OWNER TO postgres;

--
-- Name: grade_grade_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.grade_grade_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.grade_grade_number_seq OWNER TO postgres;

--
-- Name: grade_grade_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.grade_grade_number_seq OWNED BY public.grade.grade_number;


--
-- Name: homework; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.homework (
    homework_number integer NOT NULL,
    homework_text text NOT NULL,
    lesson_id integer NOT NULL,
    date date DEFAULT CURRENT_DATE NOT NULL
);


ALTER TABLE public.homework OWNER TO postgres;

--
-- Name: homework_homework_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.homework_homework_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.homework_homework_number_seq OWNER TO postgres;

--
-- Name: homework_homework_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.homework_homework_number_seq OWNED BY public.homework.homework_number;


--
-- Name: homeworkcomment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.homeworkcomment (
    comment_number integer NOT NULL,
    login character varying(30) NOT NULL,
    homework_number integer NOT NULL,
    date date DEFAULT CURRENT_DATE NOT NULL,
    comment text NOT NULL
);


ALTER TABLE public.homeworkcomment OWNER TO postgres;

--
-- Name: homeworkcomment_comment_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.homeworkcomment_comment_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.homeworkcomment_comment_number_seq OWNER TO postgres;

--
-- Name: homeworkcomment_comment_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.homeworkcomment_comment_number_seq OWNED BY public.homeworkcomment.comment_number;


--
-- Name: login; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.login (
    login_number integer NOT NULL,
    username character varying(255),
    password character varying(255),
    role character varying(255)
);


ALTER TABLE public.login OWNER TO postgres;

--
-- Name: login_login_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.login_login_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.login_login_number_seq OWNER TO postgres;

--
-- Name: login_login_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.login_login_number_seq OWNED BY public.login.login_number;


--
-- Name: notification; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification (
    notification_number integer NOT NULL,
    date date DEFAULT CURRENT_DATE NOT NULL,
    class_number integer NOT NULL,
    employee_number integer NOT NULL,
    description character varying(200) NOT NULL
);


ALTER TABLE public.notification OWNER TO postgres;

--
-- Name: notification_notification_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_notification_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notification_notification_number_seq OWNER TO postgres;

--
-- Name: notification_notification_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_notification_number_seq OWNED BY public.notification.notification_number;


--
-- Name: schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schedule (
    schedule_id integer NOT NULL,
    class_number integer NOT NULL,
    timetable_id integer NOT NULL,
    subject_number integer NOT NULL,
    day character varying(9) NOT NULL,
    CONSTRAINT schedule_day_check CHECK (((day)::text = ANY ((ARRAY['Monday'::character varying, 'Tuesday'::character varying, 'Wednesday'::character varying, 'Thursday'::character varying, 'Friday'::character varying])::text[]))),
    CONSTRAINT schedule_subject_number_check CHECK (((subject_number >= 1) AND (subject_number <= 8)))
);


ALTER TABLE public.schedule OWNER TO postgres;

--
-- Name: schedule_schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schedule_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schedule_schedule_id_seq OWNER TO postgres;

--
-- Name: schedule_schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schedule_schedule_id_seq OWNED BY public.schedule.schedule_id;


--
-- Name: student; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.student (
    login character varying(30) NOT NULL,
    full_name character varying(30) NOT NULL,
    class_number integer NOT NULL,
    CONSTRAINT student_full_name_check CHECK (((full_name)::text ~ '^[a-zA-Zа-яА-Я\s]'::text))
);


ALTER TABLE public.student OWNER TO postgres;

--
-- Name: subject; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subject (
    subject_number integer NOT NULL,
    subject_name character varying(30) NOT NULL,
    CONSTRAINT subject_subject_name_check CHECK (((subject_name)::text ~ '^[a-zA-Zа-яА-Я]'::text))
);


ALTER TABLE public.subject OWNER TO postgres;

--
-- Name: subject_subject_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.subject_subject_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subject_subject_number_seq OWNER TO postgres;

--
-- Name: subject_subject_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.subject_subject_number_seq OWNED BY public.subject.subject_number;


--
-- Name: teacher; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.teacher (
    employee_number integer NOT NULL,
    login character varying(30) NOT NULL,
    full_name character varying(30) NOT NULL,
    class_number integer,
    CONSTRAINT teacher_full_name_check CHECK (((full_name)::text ~ '^[a-zA-Zа-яА-Я.\s]'::text))
);


ALTER TABLE public.teacher OWNER TO postgres;

--
-- Name: teacher_employee_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.teacher_employee_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.teacher_employee_number_seq OWNER TO postgres;

--
-- Name: teacher_employee_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.teacher_employee_number_seq OWNED BY public.teacher.employee_number;


--
-- Name: timetable; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.timetable (
    timetable_id integer NOT NULL,
    subject_number integer NOT NULL,
    employee_number integer NOT NULL
);


ALTER TABLE public.timetable OWNER TO postgres;

--
-- Name: timetable_timetable_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.timetable_timetable_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.timetable_timetable_id_seq OWNER TO postgres;

--
-- Name: timetable_timetable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.timetable_timetable_id_seq OWNED BY public.timetable.timetable_id;


--
-- Name: total_classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.total_classes (
    count bigint
);


ALTER TABLE public.total_classes OWNER TO postgres;

--
-- Name: total_grades; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.total_grades (
    count bigint
);


ALTER TABLE public.total_grades OWNER TO postgres;

--
-- Name: total_homeworks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.total_homeworks (
    count bigint
);


ALTER TABLE public.total_homeworks OWNER TO postgres;

--
-- Name: classes class_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes ALTER COLUMN class_number SET DEFAULT nextval('public.classes_class_number_seq'::regclass);


--
-- Name: grade grade_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grade ALTER COLUMN grade_number SET DEFAULT nextval('public.grade_grade_number_seq'::regclass);


--
-- Name: homework homework_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homework ALTER COLUMN homework_number SET DEFAULT nextval('public.homework_homework_number_seq'::regclass);


--
-- Name: homeworkcomment comment_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homeworkcomment ALTER COLUMN comment_number SET DEFAULT nextval('public.homeworkcomment_comment_number_seq'::regclass);


--
-- Name: login login_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login ALTER COLUMN login_number SET DEFAULT nextval('public.login_login_number_seq'::regclass);


--
-- Name: notification notification_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification ALTER COLUMN notification_number SET DEFAULT nextval('public.notification_notification_number_seq'::regclass);


--
-- Name: schedule schedule_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule ALTER COLUMN schedule_id SET DEFAULT nextval('public.schedule_schedule_id_seq'::regclass);


--
-- Name: subject subject_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subject ALTER COLUMN subject_number SET DEFAULT nextval('public.subject_subject_number_seq'::regclass);


--
-- Name: teacher employee_number; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher ALTER COLUMN employee_number SET DEFAULT nextval('public.teacher_employee_number_seq'::regclass);


--
-- Name: timetable timetable_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timetable ALTER COLUMN timetable_id SET DEFAULT nextval('public.timetable_timetable_id_seq'::regclass);


--
-- Name: classes classes_class_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_class_name_key UNIQUE (class_name);


--
-- Name: classes classes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_pkey PRIMARY KEY (class_number);


--
-- Name: grade grade_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_pkey PRIMARY KEY (grade_number);


--
-- Name: homework homework_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homework
    ADD CONSTRAINT homework_pkey PRIMARY KEY (homework_number);


--
-- Name: homeworkcomment homeworkcomment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homeworkcomment
    ADD CONSTRAINT homeworkcomment_pkey PRIMARY KEY (comment_number);


--
-- Name: login login_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login
    ADD CONSTRAINT login_pkey PRIMARY KEY (login_number);


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (notification_number);


--
-- Name: schedule schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_pkey PRIMARY KEY (schedule_id);


--
-- Name: student student_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_pkey PRIMARY KEY (login);


--
-- Name: subject subject_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subject
    ADD CONSTRAINT subject_pkey PRIMARY KEY (subject_number);


--
-- Name: teacher teacher_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher
    ADD CONSTRAINT teacher_login_key UNIQUE (login);


--
-- Name: teacher teacher_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher
    ADD CONSTRAINT teacher_pkey PRIMARY KEY (employee_number);


--
-- Name: timetable timetable_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timetable
    ADD CONSTRAINT timetable_pkey PRIMARY KEY (timetable_id);


--
-- Name: schedule check_schedule_conflict_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER check_schedule_conflict_trigger BEFORE INSERT OR UPDATE ON public.schedule FOR EACH ROW EXECUTE FUNCTION public.check_schedule_conflict();


--
-- Name: grade grade_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.schedule(schedule_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: grade grade_login_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_login_fkey FOREIGN KEY (login) REFERENCES public.student(login) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: homework homework_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homework
    ADD CONSTRAINT homework_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.schedule(schedule_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: homeworkcomment homeworkcomment_homework_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homeworkcomment
    ADD CONSTRAINT homeworkcomment_homework_number_fkey FOREIGN KEY (homework_number) REFERENCES public.homework(homework_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: homeworkcomment homeworkcomment_login_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.homeworkcomment
    ADD CONSTRAINT homeworkcomment_login_fkey FOREIGN KEY (login) REFERENCES public.student(login) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: notification notification_class_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_class_number_fkey FOREIGN KEY (class_number) REFERENCES public.classes(class_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: notification notification_employee_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_employee_number_fkey FOREIGN KEY (employee_number) REFERENCES public.teacher(employee_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: schedule schedule_class_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_class_number_fkey FOREIGN KEY (class_number) REFERENCES public.classes(class_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: schedule schedule_timetable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_timetable_id_fkey FOREIGN KEY (timetable_id) REFERENCES public.timetable(timetable_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: student student_class_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_class_number_fkey FOREIGN KEY (class_number) REFERENCES public.classes(class_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: teacher teacher_class_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teacher
    ADD CONSTRAINT teacher_class_number_fkey FOREIGN KEY (class_number) REFERENCES public.classes(class_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: timetable timetable_employee_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timetable
    ADD CONSTRAINT timetable_employee_number_fkey FOREIGN KEY (employee_number) REFERENCES public.teacher(employee_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: timetable timetable_subject_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timetable
    ADD CONSTRAINT timetable_subject_number_fkey FOREIGN KEY (subject_number) REFERENCES public.subject(subject_number) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: TABLE classes; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.classes TO administrator;
GRANT SELECT ON TABLE public.classes TO teacher;
GRANT SELECT ON TABLE public.classes TO student;


--
-- Name: SEQUENCE classes_class_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.classes_class_number_seq TO administrator_user;


--
-- Name: TABLE grade; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,DELETE ON TABLE public.grade TO administrator;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.grade TO teacher;
GRANT SELECT ON TABLE public.grade TO student;


--
-- Name: SEQUENCE grade_grade_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.grade_grade_number_seq TO teacher;


--
-- Name: TABLE homework; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,DELETE ON TABLE public.homework TO administrator;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.homework TO teacher;
GRANT SELECT ON TABLE public.homework TO student;


--
-- Name: SEQUENCE homework_homework_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.homework_homework_number_seq TO teacher;


--
-- Name: TABLE homeworkcomment; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,DELETE ON TABLE public.homeworkcomment TO administrator;
GRANT SELECT,INSERT,DELETE ON TABLE public.homeworkcomment TO teacher;
GRANT SELECT ON TABLE public.homeworkcomment TO student;


--
-- Name: SEQUENCE homeworkcomment_comment_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.homeworkcomment_comment_number_seq TO teacher;


--
-- Name: TABLE login; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT ON TABLE public.login TO connect_user;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.login TO administrator_user;


--
-- Name: SEQUENCE login_login_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.login_login_number_seq TO administrator_user;


--
-- Name: TABLE notification; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,DELETE ON TABLE public.notification TO administrator;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.notification TO teacher;
GRANT SELECT ON TABLE public.notification TO student;


--
-- Name: SEQUENCE notification_notification_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.notification_notification_number_seq TO teacher;


--
-- Name: TABLE schedule; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE ON TABLE public.schedule TO administrator;
GRANT SELECT ON TABLE public.schedule TO teacher;
GRANT SELECT ON TABLE public.schedule TO student;


--
-- Name: SEQUENCE schedule_schedule_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.schedule_schedule_id_seq TO administrator_user;


--
-- Name: TABLE student; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.student TO administrator;
GRANT SELECT ON TABLE public.student TO teacher;
GRANT SELECT ON TABLE public.student TO student;


--
-- Name: TABLE subject; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.subject TO administrator;
GRANT SELECT ON TABLE public.subject TO teacher;
GRANT SELECT ON TABLE public.subject TO student;


--
-- Name: SEQUENCE subject_subject_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.subject_subject_number_seq TO administrator_user;


--
-- Name: TABLE teacher; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.teacher TO administrator;
GRANT SELECT ON TABLE public.teacher TO teacher;
GRANT SELECT ON TABLE public.teacher TO student;


--
-- Name: SEQUENCE teacher_employee_number_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT USAGE ON SEQUENCE public.teacher_employee_number_seq TO administrator_user;


--
-- Name: TABLE timetable; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.timetable TO administrator;
GRANT SELECT ON TABLE public.timetable TO teacher;
GRANT SELECT ON TABLE public.timetable TO student;


--
-- PostgreSQL database dump complete
--

